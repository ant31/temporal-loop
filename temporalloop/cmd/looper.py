#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer

from temporalloop.config import LOGGING_CONFIG, Config, WorkerConfig
from temporalloop.config_loader import load_config_from_yaml
from temporalloop.worker import Looper

from .models import LogLevel

STARTUP_FAILURE = 3

logger = logging.getLogger("temporalloop.info")

app = typer.Typer()


def run(config: Config) -> None:
    looper = Looper(config=config)
    asyncio.run(looper.run())


# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
@app.command(context_settings={"auto_envvar_prefix": "TEMPORALRUNNER"})
def main(
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
            show_default=True,
        ),
    ] = "default",
    host: Annotated[
        str | None,
        typer.Option("--host", help="Address of the Temporal Frontend", show_default=True),
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
            help="Workflow managed by the worker: python.module:WorkflowClass. repeat the option -w to add more workflows",
        ),
    ] = None,
    activity: Annotated[
        list[str] | None,
        typer.Option(
            "--activity",
            "-a",
            help="Activity function managed by the worker: python.module:activity_function. repeat the option -a to add more activities",
        ),
    ] = None,
    interceptor: Annotated[
        list[str] | None,
        typer.Option(
            "--interceptor",
            "-i",
            help="Interceptor class to add, python.module:InterceptorClass. repeat the option -i to add more interceptors",
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
        _config = load_config_from_yaml(str(config))
        if host:
            _config.host = host
        if namespace:
            _config.namespace = namespace
        if log_level:
            _config.log_level = log_level.value
        if log_config:
            _config.log_config = str(log_config)
        if use_colors is not None:
            _config.use_colors = use_colors
    else:
        worker_config = WorkerConfig(
            name="default-worker",
            workflows=workflow,
            activities=activity,
            queue=queue,
        )
        _config = Config(
            host=host,
            namespace=namespace,
            workers=[worker_config],
            interceptors=interceptor,
            use_colors=use_colors,
            log_config=LOGGING_CONFIG if log_config is None else str(log_config),
            log_level=log_level.value,
        )
    run(_config)


if __name__ == "__main__":
    app()
