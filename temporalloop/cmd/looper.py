#!/usr/bin/env python3
import asyncio
import logging
import platform

import click

import temporalloop
from temporalloop.config import LOG_LEVELS, LOGGING_CONFIG, Config, WorkerConfig
from temporalloop.config_loader import load_config_from_yaml
from temporalloop.worker import Looper

LEVEL_CHOICES = click.Choice(list(LOG_LEVELS.keys()))

STARTUP_FAILURE = 3

logger = logging.getLogger("temporalloop.info")


def print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    _ = param
    if not value or ctx.resilient_parsing:
        return
    click.echo(
        (
            f"Running temporalloop {temporalloop.__version__},",
            f"with {platform.python_implementation()} {platform.python_version()}",
            f"on {platform.system()},",
        )
    )
    ctx.exit()


def run(config: Config) -> None:
    looper = Looper(config=config)
    asyncio.run(looper.run())


# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
@click.command(context_settings={"auto_envvar_prefix": "TEMPORALRUNNER"})
@click.option(
    "--config",
    "-c,",
    type=click.Path(exists=True),
    default=None,
    help="Configuration file in YAML format.",
    show_default=True,
)
@click.option(
    "--namespace",
    "-n",
    type=str,
    default="default",
    help="temporalio namespace",
    show_default=True,
)
@click.option(
    "--host",
    type=str,
    default=None,
    help="Address of the Temporal Frontend",
    show_default=True,
)
@click.option(
    "--queue",
    "-q",
    type=str,
    default=None,
    help="Queue to listen on",
    show_default=True,
)
@click.option(
    "--workflow",
    "-w",
    default=[],
    multiple=True,
    help="Workflow managed by the worker: python.module:WorkflowClass. repeat the option -w to add more workflows",
)
@click.option(
    "--activity",
    "-a",
    default=[],
    multiple=True,
    help="Activity function managed by the worker:"
    + "python.module:activity_function. repeat the option -a to add more activities",
)
@click.option(
    "--interceptor",
    "-i",
    default=[],
    multiple=True,
    help="Interceptor class to add, python.module:InterceptorClass. repeat the option -i to add more interceptors",
)
@click.option(
    "--log-config",
    type=click.Path(exists=True),
    default=None,
    help="Logging configuration file. Supported formats: .ini, .json, .yaml.",
    show_default=True,
)
@click.option(
    "--log-level",
    type=LEVEL_CHOICES,
    default=None,
    help="Log level. [default: info]",
    show_default=True,
)
@click.option(
    "--use-colors/--no-use-colors",
    is_flag=True,
    default=None,
    help="Enable/Disable colorized logging.",
)
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Display the temporalloop version and exit.",
)
def main(
    config: str,
    host: str,
    queue: str,
    namespace: str,
    use_colors: bool,
    log_level: str,
    log_config: str,
    activity: list[str],
    workflow: list[str],
    interceptor: list[str],
) -> None:
    if config:
        _config = load_config_from_yaml(config)
        if host:
            _config.host = host
        if namespace:
            _config.namespace = namespace
        if log_level:
            _config.log_level = log_level
        if log_config:
            _config.log_config = log_config
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
            log_config=LOGGING_CONFIG if log_config is None else log_config,
            log_level=log_level,
        )
    run(_config)


if __name__ == "__main__":
    main()  # pragma: no cover
