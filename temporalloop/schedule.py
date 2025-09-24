import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Literal

from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleHandle,
    ScheduleIntervalSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleState,
    ScheduleUpdate,
)
from temporalio.service import RPCError, RPCStatusCode

from temporalloop.config import Config, TemporalSchedule
from temporalloop.importer import ImportFromStringError, import_from_string

logger = logging.getLogger(__name__)


@dataclass
class ScheduleDefinition:
    schedule: Schedule | None = None
    state: Literal["created", "deleted", "paused"] = "created"


class TemporalScheduler:
    def __init__(self, client, schedules_entries: dict[str, TemporalSchedule], config: Config | None = None) -> None:
        self.client = client
        self.config = config
        self.schedules: dict[str, ScheduleDefinition] = {}
        self.errors: list[Exception] = []
        self.prep_schedules(schedules_entries)

    def load_workflow(self, name: str):
        return import_from_string(name)

    def load_input(self, name: str, data: dict[str, Any]):
        if not name:
            return data
        datacls = import_from_string(name)
        return datacls.model_validate(data)

    def prep_schedule(self, schedule_id: str, schedule: TemporalSchedule) -> None:
        if schedule_id in self.schedules:
            raise ValueError(f"Duplicate schedule id: {schedule_id}")

        workflow = self.load_workflow(schedule.workflow)
        workflow_input = self.load_input(schedule.input_schema, schedule.payload)
        pause = schedule.state == "paused"

        if schedule.state == "deleted":
            sch = None
        else:
            sch = Schedule(
                action=ScheduleActionStartWorkflow(
                    workflow.run,
                    workflow_input,
                    id=schedule.workflow_id,
                    task_queue=schedule.task_queue,
                ),
                policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.BUFFER_ONE),
                spec=ScheduleSpec(
                    intervals=[
                        ScheduleIntervalSpec(
                            every=schedule.interval.every_timedelta(),
                            offset=schedule.interval.offset_timedelta(),
                        ),
                    ],
                ),
                state=ScheduleState(note=schedule.comment, paused=pause),
            )
        self.schedules[schedule_id] = ScheduleDefinition(schedule=sch, state=schedule.state)

    def prep_schedules(self, schedules: dict[str, TemporalSchedule]) -> None:
        for schedule_id, schedule in schedules.items():
            try:
                self.prep_schedule(schedule_id, schedule)
            except (ImportFromStringError, ValueError, AttributeError) as e:
                err_msg = f"Failed to prepare schedule '{schedule_id}': {e}"
                logger.error(err_msg)
                self.errors.append(Exception(err_msg))

    async def get_schedule_handle(self, schedule_id: str) -> ScheduleHandle | None:
        """Get schedule by its ID
        Returns None if schedule is not found
        """
        try:
            handle = self.client.get_schedule_handle(schedule_id)
            _ = await handle.describe()
            return handle
        except RPCError as exc:
            if exc.status in [RPCStatusCode.NOT_FOUND]:
                logger.info("Schedule %s is absent", schedule_id)
                return None
            logger.error("unexpected error: %s", exc)
            raise exc

    async def created_schedule(self, schedule_id: str, schedule: Schedule) -> ScheduleHandle:
        """Create or Update existing schedule"""
        handle = await self.get_schedule_handle(schedule_id)
        if handle is None:
            logger.info("[%s] Creating schedule", schedule_id)
            return await self.client.create_schedule(id=schedule_id, schedule=schedule)
        logger.info("[%s] Updating schedule", schedule_id)
        await handle.update(lambda _: ScheduleUpdate(schedule=schedule))
        return handle

    async def paused_schedule(self, schedule_id: str, schedule) -> ScheduleHandle:
        """Pause schedule if exists, otherwise creates it and pause it"""
        handle = await self.get_schedule_handle(schedule_id)
        if handle is not None:
            logger.info("[%s] Pausing schedule", schedule_id)
            await handle.pause()
        else:
            logger.info("[%s] Pause, Schedule is absent", schedule_id)
            handle = await self.created_schedule(schedule_id, schedule)
        return handle

    async def deleted_schedule(self, schedule_id: str) -> bool:
        """Delete schedule if exists"""
        handle = await self.get_schedule_handle(schedule_id)
        if handle is not None:
            logger.info("[%s] Deleting schedule", schedule_id)
            await handle.delete()
            return True
        logger.info("[%s] Schedule is already deleted", schedule_id)
        return False

    async def sync_schedules(self):
        if self.errors:
            error_details = "\n".join(f"- {e}" for e in self.errors)
            raise RuntimeError(f"Aborting sync due to preparation errors:\n{error_details}")

        handlers = []
        for schedule_id, schedule in self.schedules.items():
            if schedule.state == "deleted":
                coro = self.deleted_schedule(schedule_id)
            elif schedule.state == "paused":
                coro = self.paused_schedule(schedule_id, schedule.schedule)
            elif schedule.state == "created":
                if schedule.schedule is None:
                    raise ValueError(f"Schedule {schedule_id} is not defined.")
                coro = self.created_schedule(schedule_id, schedule.schedule)
            else:
                # This should be caught during prep, but is a safeguard.
                raise ValueError(f"Unknown state {schedule.state} for schedule {schedule_id}")
            handlers.append(coro)
        return await asyncio.gather(*handlers)
