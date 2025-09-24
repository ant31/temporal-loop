# Programmatic Usage

While the `temporalloop` CLI is convenient for many use cases, you can also embed and run TemporalLoop directly within your Python application. This is useful for integrating Temporal workers into a larger service or for more complex initialization logic.

The main classes you'll interact with are:

-   `temporalloop.config.Config`: The main Pydantic-based configuration object.
-   `temporalloop.worker.Looper`: The engine that runs the workers.

## Basic Example

Here's how to create and run a worker programmatically. This is equivalent to using a `config.yaml` file and the CLI.

```python
# main.py
import asyncio
from temporalloop.config import Config
from temporalloop.worker import Looper

async def main():
    # Create the main configuration object using a dictionary
    config_data = {
        "temporalio": {
            "host": "localhost:7233",
            "namespace": "default",
            "workers": [
                {
                    "name": "greeting-worker",
                    "queue": "greeting-queue",
                    "workflows": ["my_project.workflows:GreetingWorkflow"],
                    "activities": ["my_project.activities:say_hello"],
                }
            ],
        }
    }
    config = Config.model_validate(config_data)

    # Create a Looper instance with the config
    looper = Looper(config)

    # Run the looper
    # This will start the workers and block until a shutdown signal is received.
    await looper.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down workers.")
```

### Key Differences from `config.yaml`

When using the programmatic approach:

-   You construct the `Config` object, typically from a dictionary that mirrors the YAML structure.
-   You must use import strings (e.g., `"my_project.workflows:GreetingWorkflow"`) for workflows, activities, etc., as the dynamic loading is part of the configuration model.
-   You are responsible for creating the `asyncio` event loop and running the `Looper`.

## Advanced Programmatic Control

### Stopping the Looper

The `looper.run()` method will run indefinitely. If you need to stop it from another part of your application (e.g., in a service that handles its own shutdown logic), you can call `looper.stop()`.

```python
async def run_and_stop_looper():
    # ... create config and looper ...

    # Run the looper in the background
    run_task = asyncio.create_task(looper.run())

    # Do other things...
    await asyncio.sleep(10)

    # Stop the looper
    print("Stopping looper...")
    await looper.stop()

    # Wait for the run task to complete
    await run_task
```

### Custom `WorkerFactory`

You can provide a custom `WorkerFactory` to control how `temporalio.worker.Worker` instances are created.

```python
from temporalloop.worker import WorkerFactory
from temporalio.client import Client

class MyWorkerFactory(WorkerFactory):
    async def client(self, config):
        # Example: Add custom gRPC metadata to the client
        return await Client.connect(
            config.host,
            namespace=config.namespace,
            rpc_metadata={"authorization": "my-secret-token"},
        )

# Then, in your config dictionary:
config_data = {
    "temporalio": {
        # ...
        "default_factory": "my_module:MyWorkerFactory",
        "workers": [
            {
                "name": "my-worker",
                "queue": "my-queue",
                # This worker will use the default factory from Config
            },
            {
                "name": "another-worker",
                "queue": "another-queue",
                "factory": "my_module:AnotherCustomFactory", # Override per-worker
            },
        ],
    }
}
config = Config.model_validate(config_data)
```
