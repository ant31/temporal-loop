#!/usr/bin/env python3
import asyncio

import click
import yaml

from temporalloop.client import tclient
from temporalloop.config import Config
from temporalloop.config_loader import TemporalScheduleSchema, load_config_from_yaml
from temporalloop.schedule import TemporalScheduler


async def run(config: Config):
    client = await tclient(config.host, config.namespace)
    sched = TemporalScheduler(client, config.schedules)
    return await sched.sync_schedules()


# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments
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
    "--schedules-file",
    "-s",
    type=str,
    default=None,
    help="Yaml file with the schedules ",
)
def scheduler(
    config: str,
    host: str,
    namespace: str,
    schedules_file: str | None,
) -> None:
    _config = load_config_from_yaml(config)
    if namespace:
        _config.namespace = namespace
    if host:
        _config.host = host

    if schedules_file:
        with open(schedules_file, encoding="utf-8") as f:
            _config.schedules = {
                key: TemporalScheduleSchema.model_validate(val)
                for key, val in yaml.safe_load(f.read())["schedules"].items()
            }
    asyncio.run(run(_config))
