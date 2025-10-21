#!/usr/bin/env python3
import json
import logging
import logging.config
from datetime import timedelta
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from temporalloop.utils import time_interval

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
    },
}

logger: logging.Logger = logging.getLogger("temporalloop.error")


class TemporalInterval(BaseModel):
    every: str = Field(default="86400s")
    offset: str | None = Field(default=None)

    def every_timedelta(self) -> timedelta:
        return time_interval(self.every)

    def offset_timedelta(self) -> timedelta | None:
        if self.offset is None:
            return None
        return time_interval(self.offset)


class TemporalSchedule(BaseModel):
    workflow_id: str
    workflow: str
    input_schema: str = ""
    task_queue: str = "default-queue"
    interval: TemporalInterval = Field(default_factory=TemporalInterval)
    comment: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    state: Literal["created", "paused", "deleted"] = "created"


class WorkerSettings(BaseModel):
    model_config = SettingsConfigDict(arbitrary_types_allowed=True)

    name: str
    queue: str
    host: str | None = None
    namespace: str | None = None
    factory: str | None = None
    workflows: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    interceptors: list[str] | None = None
    converter: str | None = None
    pre_init: list[str] | None = None
    max_concurrent_activities: int | None = None
    max_concurrent_workflow_tasks: int | None = None
    metric_bind_address: str | None = None
    enable_metrics: bool | None = None
    debug_mode: bool = False
    disable_eager_activity_execution: bool = True


class TemporalSettings(BaseModel):
    host: str = "127.0.0.1:7233"
    namespace: str = "default"
    default_factory: str = "temporalloop.worker:WorkerFactory"
    interceptors: list[str] = Field(default_factory=list)
    converter: str | None = None
    pre_init: list[str] = Field(default_factory=list)
    max_concurrent_activities: int = 100
    max_concurrent_workflow_tasks: int = 100
    metric_bind_address: str = "0.0.0.0:9000"
    enable_metrics: bool = False
    workers: list[WorkerSettings] = Field(default_factory=list)

    def inherit_worker_settings(self) -> "TemporalSettings":
        for worker in self.workers:
            # Apply settings from the top level to each worker if not already set.
            # This ensures that CLI overrides are propagated correctly.
            if worker.host is None:
                worker.host = self.host

            if worker.namespace is None:
                worker.namespace = self.namespace
            if worker.factory is None:
                worker.factory = self.default_factory
            if worker.converter is None:
                worker.converter = self.converter
            if worker.interceptors is None:
                worker.interceptors = self.interceptors
            if worker.pre_init is None:
                worker.pre_init = self.pre_init
            if worker.max_concurrent_activities is None:
                worker.max_concurrent_activities = self.max_concurrent_activities
            if worker.max_concurrent_workflow_tasks is None:
                worker.max_concurrent_workflow_tasks = self.max_concurrent_workflow_tasks
            if worker.metric_bind_address is None:
                worker.metric_bind_address = self.metric_bind_address
            if worker.enable_metrics is None:
                worker.enable_metrics = self.enable_metrics
        return self


class LoggingSettings(BaseModel):
    level: str = "INFO"
    use_colors: bool = True
    log_config: str | dict[str, Any] | None = Field(default_factory=lambda: LOGGING_CONFIG)


class Config(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    temporalio: TemporalSettings = Field(default_factory=TemporalSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    schedules: dict[str, TemporalSchedule] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _inherit_worker_settings(self) -> "Config":
        self.temporalio.inherit_worker_settings()
        return self

    def configure_logging(self) -> None:
        log_config = self.logging.log_config
        if log_config:
            if isinstance(log_config, dict):
                if self.logging.use_colors in (True, False):
                    log_config["formatters"]["default"]["use_colors"] = self.logging.use_colors
                logging.config.dictConfig(log_config)
            elif log_config.endswith(".json"):
                with open(log_config, encoding="utf-8") as file:
                    loaded_config = json.load(file)
                    logging.config.dictConfig(loaded_config)
            elif log_config.endswith((".yaml", ".yml")):
                with open(log_config, encoding="utf-8") as file:
                    loaded_config = yaml.safe_load(file)
                    logging.config.dictConfig(loaded_config)
            else:
                logging.config.fileConfig(log_config, disable_existing_loggers=False)

        if self.logging.level:
            level = LOG_LEVELS[self.logging.level.lower()]
            logging.getLogger("temporalloop").setLevel(level)
            logging.getLogger("temporalio").setLevel(level)

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.model_validate(data)
