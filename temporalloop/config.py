#!/usr/bin/env python3
import json
import logging
import logging.config
import sys
from collections.abc import Callable, Sequence
from typing import Any, Optional, cast

import yaml
from temporalio.converter import DataConverter
from temporalio.worker import Interceptor

from temporalloop.importer import ImportFromStringError, import_from_string
from temporalloop.worker import WorkerFactory, WorkerFactoryType

LOG_LEVELS: dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "temporalloop.logutils.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "INFO",
        },
    },
    "loggers": {
        "temporalio": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "temporalloop": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "temporalloop.error": {"level": "INFO"},
    },
}

logger: logging.Logger = logging.getLogger("temporalloop.error")


def merge_loggers(logging_config: dict[str, Any]) -> dict[str, Any]:
    if "loggers" not in logging_config:
        logging_config["loggers"] = LOGGING_CONFIG["loggers"]
    else:
        if "temporalio" not in logging_config["loggers"]:
            logging_config["loggers"]["temporalio"] = LOGGING_CONFIG["loggers"]["temporalio"]
        if "temporalloop" not in logging_config["loggers"]:
            logging_config["loggers"]["temporalloop"] = LOGGING_CONFIG["loggers"]["temporalloop"]
        if "temporalloop.error" not in logging_config["loggers"]:
            logging_config["loggers"]["temporalloop.error"] = LOGGING_CONFIG["loggers"]["temporalloop.error"]

    return logging_config


# pylint: disable=too-many-arguments,too-many-instance-attributes,dangerous-default-value,invalid-name,too-many-locals
class WorkerConfig:
    def __init__(
        self,
        *,
        name: str = "worker",
        factory: type[WorkerFactoryType] | str = "",
        queue: str = "default-queue",
        host: str = "",
        namespace: str = "",
        activities: Sequence[Callable[..., Any] | str] = [],
        workflows: Sequence[type[Any] | str] = [],
        interceptors: Sequence[type[Interceptor] | str] = [],
        converter: DataConverter | str | None = None,
        pre_init: Sequence[Callable[..., Any] | str] = [],
        behavior: str = "merge",
        max_concurrent_workflow_tasks: int = 0,
        max_concurrent_activities: int = 0,
        metric_bind_address: str = "",
        enable_metrics: bool = False,
        debug_mode: bool = False,
        disable_eager_activity_execution: bool = True,
    ) -> None:
        self.name = name
        self.host: str = host
        self.namespace: str = namespace
        self.factory = WorkerFactory
        self._factory = factory
        self._workflows = workflows
        self._activities = activities
        self._interceptors = interceptors
        self._converter = converter
        self._pre_init = pre_init

        self.pre_init: list[Callable[..., Any]] = []
        self.converter: DataConverter | None = None
        self.queue = queue
        self.workflows: Sequence[type[Any]] = []
        self.interceptors: Sequence[type[Interceptor]] = []
        self.activities: Sequence[Callable[..., Any]] = []
        self.loaded = False
        self.behavior = behavior
        self.max_concurrent_workflow_tasks = max_concurrent_workflow_tasks
        self.max_concurrent_activities = max_concurrent_activities
        self.debug_mode = debug_mode
        self.disable_eager_activity_execution = disable_eager_activity_execution
        self.metric_bind_address = metric_bind_address
        self.enable_metrics = enable_metrics

    def _merge(self, config: "Config") -> None:
        if not self.host:
            self.host = config.host
        if not self.namespace:
            self.namespace = config.namespace
        if not self._factory:
            self._factory = config.factory
        if not self._converter:
            self._converter = config.converter
        if not self._interceptors:
            self._interceptors = config.interceptors
        if not self._pre_init:
            self._pre_init = config.pre_init
        if not self.max_concurrent_workflow_tasks:
            self.max_concurrent_workflow_tasks = config.max_concurrent_workflow_tasks
        if not self.max_concurrent_activities:
            self.max_concurrent_activities = config.max_concurrent_activities
        if not self.metric_bind_address:
            self.metric_bind_address = config.metric_bind_address
        if not self.enable_metrics:
            self.enable_metrics = config.enable_metrics

    def load(self, global_config: Optional["Config"] = None) -> None:
        assert not self.loaded
        if self.behavior == "merge" and global_config is not None:
            self._merge(global_config)

        self.activities = self._load_functions(self._activities)
        self.workflows = self._load_functions(self._workflows)
        self.interceptors = self._load_functions(self._interceptors)
        self.converter = cast(DataConverter, self._load_function(self._converter))
        self.factory = self._load_function(self._factory)
        self.pre_init = self._load_function(self._pre_init)
        self.loaded = True

    def _load_functions(self, functions: Sequence[Any]) -> Sequence[Any]:
        return [self._load_function(f) for f in functions]

    def _load_function(self, function: Any) -> Any:
        if isinstance(function, str):
            try:
                function = import_from_string(function)
            except ImportFromStringError as e:
                logger.error(e)
                sys.exit(1)
        return function


class Config:
    def __init__(
        self,
        *,
        host: str = "localhost:7233",
        namespace: str = "default",
        factory: type[WorkerFactoryType] | str = WorkerFactory,
        log_config: dict[str, Any] | str | None = LOGGING_CONFIG,
        log_level: str | int | None = None,
        interceptors: Sequence[type[Interceptor] | str] = [],
        converter: DataConverter | str | None = None,
        use_colors: bool | None = None,
        workers: Sequence[WorkerConfig | dict[str, Any]] = [],
        max_concurrent_activities: int = 100,
        max_concurrent_workflow_tasks: int = 100,
        metric_bind_address: str = "0.0.0.0:9000",
        limit_concurrency: int | None = None,
        pre_init: list[str] | None = None,
        enable_metrics: bool = False,
        config_logging: bool = True,
        schedules: dict[str, Any] | None = None,
    ):
        self.host = host
        self.namespace: str = namespace
        self.factory = factory
        self.log_config = log_config
        self.log_level = log_level
        self.use_colors = use_colors
        self.limit_concurrency = limit_concurrency
        self.interceptors = interceptors
        self._workers = workers
        if schedules is None:
            schedules = {}
        self.schedules = schedules
        if pre_init is None:
            pre_init = []
        self.pre_init = pre_init
        self.workers: list[WorkerConfig] = []
        self.converter = converter
        self.max_concurrent_activities = max_concurrent_activities
        self.max_concurrent_workflow_tasks = max_concurrent_workflow_tasks
        self.loaded = False
        self.enable_metrics = enable_metrics
        self.metric_bind_address = metric_bind_address
        if config_logging:
            self.configure_logging()

    def configure_logging(self) -> None:
        if self.log_config is not None:
            if isinstance(self.log_config, dict):
                if self.use_colors in (True, False):
                    self.log_config["formatters"]["default"]["use_colors"] = self.use_colors
                logging.config.dictConfig(self.log_config)
            elif self.log_config.endswith(".json"):
                with open(self.log_config, encoding="utf-8") as file:
                    loaded_config = json.load(file)
                    logging.config.dictConfig(loaded_config)
            elif self.log_config.endswith((".yaml", ".yml")):
                with open(self.log_config, encoding="utf-8") as file:
                    loaded_config = yaml.safe_load(file)
                    logging.config.dictConfig(loaded_config)
            else:
                # See the note about fileConfig() here:
                # https://docs.python.org/3/library/logging.config.html#configuration-file-format
                logging.config.fileConfig(self.log_config, disable_existing_loggers=False)

        if self.log_level is not None:
            if isinstance(self.log_level, str):
                log_level = LOG_LEVELS[self.log_level.lower()]
            else:
                log_level = self.log_level
            logging.getLogger("temporalloop.error").setLevel(log_level)
            logging.getLogger("temporalloop").setLevel(log_level)
            logging.getLogger("temporalio").setLevel(log_level)
            logging.getLogger("root").setLevel(log_level)
            logging.getLogger("temporalloop.worker").setLevel(log_level)

    def load(self) -> None:
        assert not self.loaded
        for worker in self._workers:
            w = worker
            if isinstance(w, dict):
                w = WorkerConfig(**w)
            if isinstance(w, WorkerConfig):
                w.load(self)
            else:
                raise ValueError("Invalid worker configuration")
            self.workers.append(w)
        self.loaded = True
