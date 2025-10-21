# Getting Started with TemporalLoop

This tutorial will guide you through setting up a simple project with TemporalLoop, from creating your first workflow and activity to running a worker.

## Prerequisites

-   Python 3.10+
-   A running Temporal.io server. You can follow the [Temporal quickstart guide](https://docs.temporal.io/self-hosted-guide/quick-install) to run one locally with Docker.

## 1. Project Structure

Let's start with a simple project structure:

```
my_temporal_project/
├── my_project/
│   ├── __init__.py
│   ├── activities.py
│   └── workflows.py
├── config.yaml
└── start_workflow.py
```

## 2. Define an Activity

In `my_project/activities.py`, define a simple activity:

```python
# my_project/activities.py
from temporalio import activity

@activity.defn
async def say_hello(name: str) -> str:
    return f"Hello, {name}!"
```

## 3. Define a Workflow

In `my_project/workflows.py`, define a workflow that calls the activity:

```python
# my_project/workflows.py
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import say_hello

@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            say_hello, name, start_to_close_timeout=timedelta(seconds=10)
        )
```

## 4. Create a Configuration File

In `config.yaml`, configure `temporalloop` to run a worker for your workflow and activity:

```yaml
# config.yaml
temporalio:
  # Connect to a local Temporal server
  host: "127.0.0.1:7233"
  namespace: "default"

  workers:
    - name: "greeting-worker"
      # The task queue this worker will listen on
    queue: "greeting-queue"
    # Link to your workflow class
    workflows:
      - "my_project.workflows:GreetingWorkflow"
    # Link to your activity function
    activities:
      - "my_project.activities:say_hello"

logging:
  level: "INFO"
```

## 5. Run the Worker

You can now start the worker using the `temporalloop` command-line tool. From your project's root directory (`my_temporal_project/`), run:

```bash
temporalloop --config=config.yaml
```

You should see output indicating that the worker has started and is polling the `greeting-queue` for tasks.

## 6. Start a Workflow Execution

To test the worker, you can start a workflow execution using a separate script. Create `start_workflow.py`:

```python
# start_workflow.py
import asyncio
from temporalio.client import Client

# Import the workflow class for type-hinting
from my_project.workflows import GreetingWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        GreetingWorkflow.run,
        "Temporal",
        id="my-first-workflow",
        task_queue="greeting-queue",
    )
    print(f"Workflow result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run this script in a separate terminal:

```bash
python start_workflow.py
```

You should see the output `Workflow result: Hello, Temporal!`, and your worker's logs will show that it processed the workflow and activity tasks.

Congratulations! You've successfully set up and run your first worker with TemporalLoop.
