#!/usr/bin/env python3
import asyncio
import dataclasses
import functools
import logging
import signal
import threading
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from types import FrameType
from typing import TYPE_CHECKING, Any, TypeVar, cast

from temporalio import workflow
from temporalio.client import Client
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from temporalloop.importer import import_from_string

if TYPE_CHECKING:
    from temporalloop.config import Config, TemporalSettings, WorkerSettings

WorkerFactoryType = TypeVar("WorkerFactoryType", bound="WorkerFactory")

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
    invalid_module_member_children = dict(SandboxRestrictions.invalid_module_members_default.children)
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
        self.new_runtime = None

    async def client(self, config: "TemporalSettings", client: Client | None = None) -> Client:
        if client:
            return client

        if config.metric_bind_address and config.enable_metrics:
            self.new_runtime = Runtime(
                telemetry=TelemetryConfig(metrics=PrometheusConfig(bind_address=config.metric_bind_address))
            )

        kwargs: dict[str, Any] = {"namespace": config.namespace}
        if self.new_runtime is not None:
            kwargs["runtime"] = self.new_runtime

        if config.converter is not None:
            kwargs["data_converter"] = config.converter

        return await Client.connect(config.host, **kwargs)

    async def execute_preinit(self, fn: list[Callable[..., Any]]) -> None:
        for x in fn:
            logger.info("[Execute][Pre-init][%s]", x)
            x()

    async def new_worker(
        self,
        worker_config: "WorkerSettings",
        client: Client,
        loaded_workflows: Sequence[type],
        loaded_activities: Sequence[Callable[..., Any]],
        loaded_interceptors: Sequence[type],
        loaded_pre_init: list[Callable[..., Any]],
    ) -> Worker:
        config = worker_config
        await self.execute_preinit(loaded_pre_init)
        logger.info(
            (
                "[Start worker][%s][queue:%s][workflows:%s]"
                "[activities:%s][max_concurrent_workflow_tasks:%s]"
                "[max_concurrent_activities:%s][metric_bind_address:%s]"
            ),
            config.name,
            config.queue,
            [w.__name__ for w in loaded_workflows],
            [a.__name__ for a in loaded_activities],
            config.max_concurrent_workflow_tasks,
            config.max_concurrent_activities,
            config.metric_bind_address,
        )
        # Run a worker for the workflow
        return Worker(
            client,
            task_queue=config.queue,
            workflows=loaded_workflows,
            activities=loaded_activities,
            disable_eager_activity_execution=config.disable_eager_activity_execution,
            max_concurrent_workflow_tasks=config.max_concurrent_workflow_tasks,
            max_concurrent_activities=config.max_concurrent_activities,
            interceptors=[x() for x in loaded_interceptors],
            activity_executor=ThreadPoolExecutor(max(config.max_concurrent_activities + 1, 10)),
            workflow_runner=new_sandbox_runner(),
            graceful_shutdown_timeout=timedelta(seconds=10),
        )


class Looper:
    def __init__(self, config: "Config"):
        self.config = config
        self.workers: list[Worker] = []
        self.should_exit = False
        self.client: Client | None = None

    @staticmethod
    @functools.cache
    def _load_function(path: str) -> Any:
        return import_from_string(path)

    def _load_functions(self, paths: Sequence[str] | None) -> list[Any]:
        if not paths:
            return []
        return [self._load_function(path) for path in paths]

    async def stop(self) -> None:
        logger.info("Worker shutdown requested")
        group = [asyncio.wait_for(x.shutdown(), 3) for x in self.workers]
        await asyncio.gather(*group)
        if self.client:
            await self.client.close()

    async def run(self):
        self.install_signal_handlers()
        self.config.configure_logging()
        logger.info("Connecting %s workers", len(self.config.temporalio.workers))
        self.workers = await self.prepare_workers()
        logger.info("Starting %s workers", len(self.config.temporalio.workers))
        await asyncio.gather(*[x.run() for x in self.workers])

    async def prepare_workers(self) -> list[Worker]:
        factory_instance = WorkerFactory(self.config)
        # Load global converter if specified
        if self.config.temporalio.converter:
            self.config.temporalio.converter = self._load_function(self.config.temporalio.converter)
        self.client = await factory_instance.client(self.config.temporalio)

        group = []
        for worker_config in self.config.temporalio.workers:
            # Load callables for the worker
            loaded_factory_class = self._load_function(worker_config.factory or self.config.temporalio.default_factory)
            loaded_workflows = self._load_functions(worker_config.workflows)
            loaded_activities = self._load_functions(worker_config.activities)
            loaded_interceptors = self._load_functions(worker_config.interceptors)
            loaded_pre_init = self._load_functions(worker_config.pre_init)
            if worker_config.converter:
                worker_config.converter = self._load_function(worker_config.converter)

            # Create factory and worker
            factory = loaded_factory_class(self.config)
            group.append(
                factory.new_worker(
                    worker_config,
                    client=self.client,
                    loaded_workflows=loaded_workflows,
                    loaded_activities=loaded_activities,
                    loaded_interceptors=loaded_interceptors,
                    loaded_pre_init=loaded_pre_init,
                )
            )
        res: list[Worker] = cast(list[Worker], await asyncio.gather(*group))
        return res

    # Start client
    def install_signal_handlers(self) -> None:
        """Install signal handlers for the signals we want to handle."""
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return
        for sig in HANDLED_SIGNALS:
            asyncio.get_running_loop().add_signal_handler(sig, self.handle_exit, sig, None)

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        """Handle exit signals by setting the interrupt event."""
        _ = frame
        if sig in (signal.SIGTERM, signal.SIGINT):
            logger.warning("Received signal %s: stopping the workers", sig)
            raise SystemExit(0)
        logger.info("Received Signal %s: ignored", sig)
