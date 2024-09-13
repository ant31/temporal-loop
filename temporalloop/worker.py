#!/usr/bin/env python3
import asyncio
import dataclasses
import logging
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from types import FrameType
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast
from temporalio.runtime import Runtime, TelemetryConfig, PrometheusConfig
from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from temporalloop.importer import import_from_string

if TYPE_CHECKING:
    from temporalloop.config import Config, WorkerConfig

WorkerFactoryType = TypeVar(  # pylint: disable=invalid-name
    "WorkerFactoryType", bound="WorkerFactory"
)

logger = logging.getLogger("temporalloop.info")

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

# We always want to pass through external modules to the sandbox that we know
# are safe for workflow use
with workflow.unsafe.imports_passed_through():
    # import are not used, but listed
    _ = import_from_string("pydantic:BaseModel")
    _ = import_from_string("temporalloop.converters.pydantic:pydantic_data_converter")


def new_sandbox_runner() -> SandboxedWorkflowRunner:
    # TODO(cretz): Use with_child_unrestricted when https://github.com/temporalio/sdk-python/issues/254
    # is fixed and released
    invalid_module_member_children = dict(
        SandboxRestrictions.invalid_module_members_default.children
    )
    del invalid_module_member_children["datetime"]
    return SandboxedWorkflowRunner(
        restrictions=dataclasses.replace(
            SandboxRestrictions.default,
            invalid_module_members=dataclasses.replace(
                SandboxRestrictions.invalid_module_members_default,
                children=invalid_module_member_children,
            ),
        )
    )


class WorkerFactory:
    def __init__(self, config: "Config"):
        self.config = config

    async def execute_preinit(self, fn: list[Callable[..., Any]]) -> None:
        for x in fn:
            logger.info("[Execute][Pre-init][%s]", x)
            x()

    async def new_worker(self, worker_config: "WorkerConfig") -> Worker:
        config = worker_config
        await self.execute_preinit(worker_config.pre_init)
        kwargs: dict[str, Any] = {"namespace": config.namespace}
        if config.metric_bind_address:
            new_runtime = Runtime(telemetry=TelemetryConfig(metrics=PrometheusConfig(bind_address=config.metric_bind_address)))
            kwargs["runtime"] = new_runtime

        if config.converter is not None:
            kwargs["data_converter"] = config.converter

        client = await Client.connect(config.host, **kwargs)

        logger.info(
            "[Start worker][%s][queue:%s][workflows:%s][activities:%s]",
            config.name,
            config.queue,
            config.workflows,
            config.activities,
        )

        # Run a worker for the workflow
        return Worker(
            client,
            task_queue=config.queue,
            workflows=config.workflows,
            activities=config.activities,
            disable_eager_activity_execution=False,
            max_concurrent_workflow_tasks=config.max_concurrent_workflow_tasks,
            max_concurrent_activities=config.max_concurrent_activities,
            interceptors=[x() for x in config.interceptors],
            activity_executor=ThreadPoolExecutor(
                max(config.max_concurrent_activities + 1, 10)
            ),
            workflow_runner=new_sandbox_runner(),
        )


class Looper:
    def __init__(self, config: "Config"):
        self.config = config
        self.workers: list[Worker] = []
        self.should_exit = False

    async def stop(self) -> None:
        logger.info("Worker shutdown requested")
        group = [x.shutdown() for x in self.workers]
        await asyncio.gather(*group)
        logger.info("Worker shutdown complete")

    async def run(self):
        self.install_signal_handlers()
        if not self.config.loaded:
            self.config.load()
        logger.info("Config loaded")
        logger.info("Connecting %s workers", len(self.config.workers))
        self.workers = await self.prepare_workers()
        logger.info("Starting %s workers", len(self.config.workers))
        await asyncio.gather(*[x.run() for x in self.workers])

    async def prepare_workers(self) -> list[Worker]:
        group = []
        for worker_config in self.config.workers:
            group.append(worker_config.factory(self.config).new_worker(worker_config))
        res: list[Worker] = cast(list[Worker], await asyncio.gather(*group))
        return res

    # Start client
    def install_signal_handlers(self) -> None:
        """Install signal handlers for the signals we want to handle."""
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return
        for sig in HANDLED_SIGNALS:
            asyncio.get_running_loop().add_signal_handler(
                sig, self.handle_exit, sig, None
            )

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        """Handle exit signals by setting the interrupt event."""
        _ = frame
        if sig in (signal.SIGTERM, signal.SIGINT):
            logger.warning("Received signal %s: stopping the workers", sig)
            asyncio.create_task(self.stop())
        else:
            logger.info("Received Signal %s: ignored", sig)
