import asyncio
import logging
import re
from datetime import timedelta
from typing import Any

import temporalio.client
from ant31box.importer import import_from_string
from temporalio.client import WorkflowHandle
from temporalio.service import RPCError, RPCStatusCode

logger = logging.getLogger(__name__)

TIMEINTERVAL_REGEX = re.compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")


def time_interval(time_str: str) -> timedelta:
    parts = TIMEINTERVAL_REGEX.match(time_str)
    if not parts:
        raise ValueError(f"Invalid time string {time_str}")
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


async def gather_with_concurrency(n, *coros):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


async def as_completed_with_concurrency(n, workflow, *coros):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    sem_coros = [sem_coro(c) for c in coros]

    if workflow is not None:
        for c in workflow.as_completed(sem_coros):
            yield c
    else:
        for c in asyncio.as_completed(sem_coros):
            yield c


async def get_handler(
    client: temporalio.client.Client,
    workflow_id: str,
    workflow_name: str,
) -> tuple[temporalio.client.WorkflowHandle[Any, Any], Any]:
    workflow = import_from_string(workflow_name)
    # Retrieve running workflow handler
    return (
        client.get_workflow_handle_for(workflow_id=workflow_id, workflow=workflow.run),
        workflow,
    )


async def find_workflow(client: temporalio.client.Client, jid: str, workflow: str) -> WorkflowHandle[Any, Any] | None:
    """Find a workflow by its ID and name. If it doesn't exist returns None"""
    handler, _ = await get_handler(client, jid, workflow)
    try:
        _ = await handler.describe()
    except RPCError as exc:
        # If it fails because the workflow is not found or already completed,
        # create a new one
        if exc.status != RPCStatusCode.NOT_FOUND:
            raise exc
        logger.info("Workflow not found; %s", exc)
        return None
    return handler
