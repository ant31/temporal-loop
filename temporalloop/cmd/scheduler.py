#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer
from temporalio.client import Client

from temporalloop.config import Config
from temporalloop.converters.pydantic import pydantic_data_converter
from temporalloop.schedule import TemporalScheduler

from .utils import load_config_with_overrides

app = typer.Typer()
logger = logging.getLogger("temporalloop.info")


async def run(config: Config):
    client = await Client.connect(
        config.temporalio.host,
        namespace=config.temporalio.namespace,
        data_converter=pydantic_data_converter,
    )
    sched = TemporalScheduler(client, config.schedules)
    try:
        await sched.sync_schedules()
        logger.info("Schedule synchronization completed successfully.")
    except RuntimeError as e:
        logger.error("Schedule synchronization failed.")
        print(e)
        raise typer.Exit(code=1) from e


@app.command(context_settings={"auto_envvar_prefix": "TEMPORALRUNNER"})
def scheduler(  # pylint: disable=too-many-arguments
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
        str | None,
        typer.Option("--host", help="Address of the Temporal Frontend", show_default=True),
    ] = None,
    namespace: Annotated[
        str | None,
        typer.Option("--namespace", "-n", help="temporalio namespace", show_default=True),
    ] = "default",
) -> None:
    _config = load_config_with_overrides(config_path=config, host=host, namespace=namespace)
    _config.configure_logging()
    asyncio.run(run(_config))
