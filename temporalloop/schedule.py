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
    wid: str = ""


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

    def prep_schedule(self, wid: str, schedule: TemporalSchedule) -> None:
        if schedule.workflow_id in self.schedules:
            raise ValueError(f"Duplicate schedule workflow_id: {schedule.workflow_id}")

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
        self.schedules[schedule.workflow_id] = ScheduleDefinition(
            schedule=sch, state=schedule.state, wid=schedule.workflow_id
        )

    def prep_schedules(self, schedules: dict[str, TemporalSchedule]) -> None:
        for wid, schedule in schedules.items():
            try:
                self.prep_schedule(wid, schedule)
            except (ImportFromStringError, ValueError, AttributeError) as e:
                err_msg = f"Failed to prepare schedule '{wid}': {e}"
                logger.error(err_msg)
                self.errors.append(Exception(err_msg))

    async def get_schedule_handle(self, wid: str) -> ScheduleHandle | None:
        """Get schedule by workflow id
        Returns None if schedule is not found
        """
        try:
            handle = self.client.get_schedule_handle(wid)
            _ = await handle.describe()
            return handle
        except RPCError as exc:
            if exc.status in [RPCStatusCode.NOT_FOUND]:
                logger.info("Schedule %s is absent", wid)
                return None
            logger.error("unexpected error: %s", exc)
            raise exc

    async def created_schedule(self, wid: str, schedule: Schedule) -> ScheduleHandle:
        """Create or Update existing schedule"""
        handle = await self.get_schedule_handle(wid)
        if handle is None:
            logger.info("[%s] Creating schedule", wid)
            return await self.client.create_schedule(id=wid, schedule=schedule)
        logger.info("[%s] Updating schedule", wid)
        await handle.update(lambda _: ScheduleUpdate(schedule=schedule))
        return handle

    async def paused_schedule(self, wid: str, schedule) -> ScheduleHandle:
        """Pause schedule if exists, otherwise creates it and pause it"""
        handle = await self.get_schedule_handle(wid)
        if handle is not None:
            logger.info("[%s] Pausing schedule", wid)
            await handle.pause()
        else:
            logger.info("[%s] Pause, Schedule is absent", wid)
            handle = await self.created_schedule(wid, schedule)
        return handle

    async def deleted_schedule(self, wid: str) -> bool:
        """Delete schedule if exists"""
        handle = await self.get_schedule_handle(wid)
        if handle is not None:
            logger.info("[%s] Deleting schedule", wid)
            await handle.delete()
            return True
        logger.info("[%s] Schedule is already deleted", wid)
        return False

    async def sync_schedules(self):
        if self.errors:
            error_details = "\n".join(f"- {e}" for e in self.errors)
            raise RuntimeError(f"Aborting sync due to preparation errors:\n{error_details}")

        handlers = []
        for wid, schedule in self.schedules.items():
            if schedule.state == "deleted":
                coro = self.deleted_schedule(wid)
            elif schedule.state == "paused":
                coro = self.paused_schedule(wid, schedule.schedule)
            elif schedule.state == "created":
                if schedule.schedule is None:
                    raise ValueError(f"Schedule {wid} is not defined.")
                coro = self.created_schedule(wid, schedule.schedule)
            else:
                # This should be caught during prep, but is a safeguard.
                raise ValueError(f"Unknown state {schedule.state} for schedule {wid}")
            handlers.append(coro)
        return await asyncio.gather(*handlers)
