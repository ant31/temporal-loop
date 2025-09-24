#!/usr/bin/env python3
import asyncio
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from temporalloop.client import tclient
from temporalloop.config import Config
from temporalloop.config_loader import TemporalScheduleSchema, load_config_from_yaml
from temporalloop.schedule import TemporalScheduler

app = typer.Typer()


async def run(config: Config):
    client = await tclient(config.host, config.namespace)
    sched = TemporalScheduler(client, config.schedules)
    return await sched.sync_schedules()


# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments
@app.command(context_settings={"auto_envvar_prefix": "TEMPORALRUNNER"})
def scheduler(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            exists=True,
            help="Configuration file in YAML format.",
            show_default=True,
        ),
    ],
    host: Annotated[
        Optional[str],
        typer.Option("--host", help="Address of the Temporal Frontend", show_default=True),
    ] = None,
    namespace: Annotated[
        Optional[str],
        typer.Option("--namespace", "-n", help="temporalio namespace", show_default=True),
    ] = "default",
    schedules_file: Annotated[
        Optional[Path],
        typer.Option("--schedules-file", "-s", help="Yaml file with the schedules "),
    ] = None,
) -> None:
    _config = load_config_from_yaml(str(config))
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
