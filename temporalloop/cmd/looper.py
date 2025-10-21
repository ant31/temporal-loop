#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer

from temporalloop.config import Config, WorkerSettings
from temporalloop.worker import Looper

from .models import LogLevel
from .utils import load_config_with_overrides

STARTUP_FAILURE = 3

logger = logging.getLogger("temporalloop.info")

app = typer.Typer()


def run(config: Config) -> None:
    looper = Looper(config=config)
    asyncio.run(looper.run())


@app.command(context_settings={"auto_envvar_prefix": "TEMPORALRUNNER"})
def main(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            exists=True,
            help="Configuration file in YAML format.",
            show_default=True,
        ),
    ] = None,
    namespace: Annotated[
        str | None,
        typer.Option(
            "--namespace",
            "-n",
            help="temporalio namespace",
        ),
    ] = None,
    host: Annotated[
        str | None,
        typer.Option("--host", help="Address of the Temporal Frontend"),
    ] = None,
    queue: Annotated[
        str | None,
        typer.Option("--queue", "-q", help="Queue to listen on", show_default=True),
    ] = None,
    workflow: Annotated[
        list[str] | None,
        typer.Option(
            "--workflow",
            "-w",
            help="Workflow managed by the worker: python.module:WorkflowClass. Repeat for more workflows.",
        ),
    ] = None,
    activity: Annotated[
        list[str] | None,
        typer.Option(
            "--activity",
            "-a",
            help="Activity: python.module:activity_function. Repeat for more activities.",
        ),
    ] = None,
    interceptor: Annotated[
        list[str] | None,
        typer.Option(
            "--interceptor",
            "-i",
            help="Interceptor class to add: python.module:InterceptorClass. Repeat for more interceptors.",
        ),
    ] = None,
    log_config: Annotated[
        Path | None,
        typer.Option(
            "--log-config",
            exists=True,
            help="Logging configuration file. Supported formats: .ini, .json, .yaml.",
            show_default=True,
        ),
    ] = None,
    log_level: Annotated[
        LogLevel,
        typer.Option(
            "--log-level",
            help="Log level.",
            show_default=True,
            case_sensitive=False,
        ),
    ] = LogLevel.info,
    use_colors: Annotated[
        bool,
        typer.Option(
            "--use-colors/--no-use-colors",
            help="Enable/Disable colorized logging.",
        ),
    ] = True,
) -> None:
    if config:
        _config = load_config_with_overrides(config_path=config, host=host, namespace=namespace)
        if log_level:
            _config.logging.level = log_level.value
        if log_config:
            _config.logging.log_config = str(log_config)
        if use_colors is not None:
            _config.logging.use_colors = use_colors
    else:
        worker_config = WorkerSettings(
            name="default-worker",
            workflows=workflow or [],
            activities=activity or [],
            queue=queue,
            interceptors=interceptor or [],
        )
        _config = Config.model_validate(
            {
                "temporalio": {
                    "host": host or "localhost:7233",
                    "namespace": namespace,
                    "interceptors": interceptor or [],
                    "workers": [worker_config.model_dump()],
                },
                "logging": {"use_colors": use_colors, "level": log_level.value},
            }
        )
        _config.temporalio.inherit_worker_settings()
    run(_config)


if __name__ == "__main__":
    app()
