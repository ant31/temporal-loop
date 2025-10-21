# Configuration

TemporalLoop uses a YAML file for configuration, providing a clear and declarative way to define your workers and their behavior. You can also configure `temporalloop` programmatically.

## YAML Configuration

The configuration file is divided into three main top-level sections: `temporalio`, `logging`, and `schedules`.

### `temporalio` Section (Global)

This section defines the global settings for your Temporal connection and default worker behavior.

```yaml
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"
  default_factory: "temporalloop.worker:WorkerFactory"
  interceptors:
    - "temporalloop.interceptors.sentry:SentryInterceptor"
  converter: "temporalloop.converters.pydantic:pydantic_data_converter"
  pre_init:
    - "my_project.setup:initialize_database"
  max_concurrent_activities: 100
  max_concurrent_workflow_tasks: 100
  metric_bind_address: "0.0.0.0:9000"
  enable_metrics: false
  disable_eager_activity_execution: true
```

-   **`host`**: The address of the Temporal Frontend.
-   **`namespace`**: The Temporal namespace to connect to.
-   **`default_factory`**: An import string for a custom `WorkerFactory` class to be used by default.
-   **`interceptors`**: A list of global interceptor import strings to be applied to all workers.
-   **`converter`**: An import string for a `DataConverter` instance to be used globally. `temporalloop` provides a Pydantic-based converter out of the box.
-   **`pre_init`**: A list of import strings for functions to be executed before workers start.
-   **`max_concurrent_activities`**: Default maximum number of concurrent activities for workers.
-   **`max_concurrent_workflow_tasks`**: Default maximum number of concurrent workflow tasks for workers.
-   **`metric_bind_address`**: The address for the Prometheus metrics endpoint.
-   **`enable_metrics`**: A boolean to enable or disable metrics globally.
-   **`disable_eager_activity_execution`**: A boolean to disable eager activity execution globally. Defaults to `true`.

### `workers` Section

This is a list under the `temporalio` key where each item defines a worker.

```yaml
temporalio:
  # ... other temporalio settings ...
  workers:
    - name: "example-worker-1"
      queue: "example-queue-1"
    workflows:
      - "your_package.workflows:YourWorkflow"
    activities:
      - "your_package.activities:your_activity_one"
    # Worker-specific overrides
    namespace: "staging"
    max_concurrent_activities: 50
    debug_mode: true
    disable_eager_activity_execution: false
```

-   **`name`**: A unique name for the worker, used for logging.
-   **`queue`**: The task queue this worker will poll.
-   **`workflows`**: A list of workflow class import strings to be registered with this worker.
-   **`activities`**: A list of activity function import strings to be registered.
-   **`debug_mode`**: A boolean to enable debug mode for the worker.
-   **`disable_eager_activity_execution`**: A boolean to disable eager activity execution for the worker.
-   **Overrides**: You can override any global setting from the `temporalio` section on a per-worker basis (e.g., `namespace`, `factory`, `interceptors`, `converter`, concurrency settings, etc.).

### `logging` Section

This section controls the logging output.

```yaml
logging:
  level: "INFO"
  use_colors: true
  log_config: "/path/to/your/logging_config.ini"
```

-   **`level`**: The log level (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `TRACE`).
-   **`use_colors`**: A boolean to enable or disable colorized logging.
-   **`log_config`**: An optional path to a standard Python logging configuration file (`.ini`, `.json`, or `.yaml`).

## Programmatic Configuration

You can also configure and run `temporalloop` directly from your Python code by creating a `Config` object.

```python
from temporalloop.config import Config
from temporalloop.worker import Looper
import asyncio

async def main():
    config_data = {
        "temporalio": {
            "host": "localhost:7233",
            "namespace": "default",
            "workers": [
                {
                    "name": "my-worker",
                    "queue": "my-queue",
                    "workflows": ["my_project.workflows:MyWorkflow"],
                    "activities": ["my_project.activities:my_activity"],
                }
            ],
        }
    }
    config = Config.model_validate(config_data)
    looper = Looper(config)
    await looper.run()

if __name__ == "__main__":
    asyncio.run(main())
```
