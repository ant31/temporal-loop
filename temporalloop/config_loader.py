from datetime import timedelta
from typing import Any, Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from temporalloop.config import LOGGING_CONFIG, Config
from temporalloop.utils import time_interval


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)


class LoggingConfigSchema(BaseConfig):
    use_colors: bool = Field(default=True)
    log_config: dict[str, Any] | str | None = Field(default_factory=lambda: LOGGING_CONFIG)
    level: str = Field(default="INFO")


class TemporalInterval(BaseConfig):
    every: str = Field(default="86400s")
    offset: str | None = Field(default=None)

    def every_timedelta(self) -> timedelta:
        return time_interval(self.every)

    def offset_timedelta(self) -> timedelta | None:
        if self.offset is None:
            return None
        return time_interval(self.offset)


class TemporalScheduleSchema(BaseConfig):
    workflow_id: str = Field(...)
    workflow: str = Field(...)
    input_schema: str = Field(default="")
    task_queue: str = Field(default="connyex-queue")
    interval: TemporalInterval = Field(default_factory=TemporalInterval)
    comment: str = Field(default="")
    payload: dict[str, Any] = Field(default_factory=dict)
    state: Literal["created", "paused", "deleted"] = Field(default="created")


class WorkerConfigSchema(BaseConfig):
    interceptors: list[str] | None = Field(default=None)
    activities: list[str] | None = Field(default=[])
    workflows: list[str] | None = Field(default=[])
    queue: str = Field(default="")
    name: str = Field(default="")
    converter: str | None = Field(default=None)
    factory: str | None = Field(default=None)
    pre_init: list[str] | None = Field(default=None)
    max_concurrent_activities: int = Field(default=100)
    max_concurrent_workflow_tasks: int = Field(default=100)
    debug_mode: bool = Field(default=False)
    disable_eager_activity_execution: bool = Field(default=True)  # pylint: disable=invalid-name
    metric_bind_address: str = Field(default="0.0.0.0:9000")
    enable_metrics: bool = Field(default=False)


class TemporalConfigSchema(BaseConfig):
    host: str = Field(default="localhost:7233")
    namespace: str = Field(default="default")
    workers: list[WorkerConfigSchema] = Field(default_factory=list)
    interceptors: list[str] = Field(default_factory=list)
    converter: str | None = Field(default=None)
    default_factory: str = Field(default="temporalloop.worker:WorkerFactory")
    pre_init: list[str] = Field(default_factory=list)
    max_concurrent_activities: int = Field(default=100)
    max_concurrent_workflow_tasks: int = Field(default=100)
    disable_eager_activity_execution: bool = Field(default=True)  # pylint: disable=invalid-name
    metric_bind_address: str = Field(default="0.0.0.0:9000")
    enable_metrics: bool = Field(default=False)


class ConfigSchema(BaseConfig):
    temporalio: TemporalConfigSchema = Field(default_factory=TemporalConfigSchema)
    logging: LoggingConfigSchema = Field(default_factory=LoggingConfigSchema)
    schedules: dict[str, TemporalScheduleSchema] = Field(default_factory=dict)


def load_config_from_yaml(file_path: str) -> Config:
    with open(file_path, encoding="utf-8") as file:
        config_dict = yaml.safe_load(file)
    return config_from_dict(config_dict)


def config_from_dict(config_dict: dict[str, Any]) -> Config:
    config = ConfigSchema()
    if "temporalio" in config_dict:
        config.temporalio = TemporalConfigSchema(**config_dict["temporalio"])
    if "logging" in config_dict:
        config.logging = LoggingConfigSchema(**config_dict["logging"])
    if "schedules" in config_dict:
        config.schedules = {x: TemporalScheduleSchema(**config_dict["schedules"][x]) for x in config_dict["schedules"]}

    # if "workers" in config_dict:
    #     config.workers = [
    #         WorkerConfigSchema(**worker) for worker in config_dict["workers"]
    #     ]
    # if "interceptors" in config_dict:
    #     config.interceptors = config_dict["interceptors"]
    # if "converter" in config_dict:
    #     config.converter = config_dict["converter"]
    # if "default_factory" in config_dict:
    #     config.default_factory = config_dict["default_factory"]

    return Config(
        host=config.temporalio.host,
        namespace=config.temporalio.namespace,
        factory=config.temporalio.default_factory,
        converter=config.temporalio.converter,
        log_level=config.logging.level,
        use_colors=config.logging.use_colors,
        log_config=config.logging.log_config,
        workers=[x.__dict__ for x in config.temporalio.workers],  # pylint: disable=not-an-iterable
        interceptors=config.temporalio.interceptors,
        pre_init=config.temporalio.pre_init,
        schedules=config.schedules,
    )
