# Client Handling

This document explains how the `temporalio.client.Client` is created and managed within TemporalLoop and how you can customize its behavior.

## Worker Client Management

When you run `temporalloop`, it automatically creates and manages `temporalio.client.Client` instances for your workers. A separate client is instantiated for each unique client configuration (e.g., different hosts, namespaces, or custom factories). Workers with identical client settings may share a client instance. This is handled internally by the `Looper`.

You don't need to create a client yourself for the workers to function; the framework handles it based on your `config.yaml`.

## Customizing the Worker Client

The recommended way to customize the client used by your workers is to provide a custom `WorkerFactory`. This gives you full control over client instantiation, allowing you to add custom gRPC metadata, mTLS certificates, or other advanced options.

### 1. Create a Custom Factory

Create a Python class that inherits from `temporalloop.worker.WorkerFactory` and override the `client` method.

```python
# my_project/factories.py
from temporalio.client import Client
from temporalloop.worker import WorkerFactory

class MyWorkerFactory(WorkerFactory):
    async def client(self, config) -> Client:
        """
        Creates a custom Temporal client.
        This example adds a static authorization token to the gRPC metadata.
        """
        return await Client.connect(
            config.host,
            namespace=config.namespace,
            rpc_metadata={"authorization": "my-secret-token"},
        )
```

### 2. Update Your Configuration

In your `config.yaml`, set the `default_factory` to point to your new class.

```yaml
# config.yaml
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"
  # Use your custom factory for all workers by default
  default_factory: "my_project.factories:MyWorkerFactory"

workers:
  # ... your workers here ...
```

You can also specify a factory on a per-worker basis if different workers need different client configurations.

## Client for Starting Workflows

When you need to start a workflow from a separate script or application (i.e., not from within a worker), you must create your own client instance. This is standard `temporalio` usage.

```python
# start_workflow.py
import asyncio
from temporalio.client import Client

# Import the workflow class for type-hinting
from my_project.workflows import GreetingWorkflow

async def main():
    # Connect to the same Temporal server your workers are using
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
