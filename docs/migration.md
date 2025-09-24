# Migration Guide

This document provides instructions for migrating between major versions of TemporalLoop.

## Migrating to v0.4.0

Version 0.4.0 introduces a major overhaul of the configuration and command-line interface. These changes are not backward-compatible and will require updates to your project.

### 1. `config.yaml` Structure

The structure of `config.yaml` has been completely redesigned. You must update your configuration file to the new format.

-   Global settings are now under a `temporalio` key.
-   Worker definitions are now a list under `temporalio.workers`.
-   Logging settings are under a `logging` key.
-   Schedules are now a top-level key `schedules`.

**Old Format:**

```yaml
# config.yaml
host: "127.0.0.1:7233"
namespace: "default"
workers:
  - name: "my-worker"
    queue: "my-task-queue"
    # ...
log_level: "INFO"
```

**New Format:**

```yaml
# config.yaml
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"
  workers:
    - name: "my-worker"
      queue: "my-task-queue"
      # ...

logging:
  level: "INFO"

schedules:
  my-schedule:
    # ...
```

### 2. CLI Command Changes

The CLI has been migrated from `click` to `typer`. While many flags are similar, their implementation has changed.

#### `scheduler` Command

-   The `--schedules-file` or `-s` option has been **removed**.
-   The `scheduler` now reads schedule definitions directly from the `schedules` section of the main configuration file provided via `--config`.

**Action Required:** Move your schedule definitions from a separate file into your main `config.yaml` under the `schedules:` key.

### 3. Programmatic Usage

The configuration classes have been completely replaced with new Pydantic models.

-   The old `temporalloop.config.Config` and `WorkerConfig` classes are gone.
-   The new main configuration class is `temporalloop.config.Config`. It is a Pydantic `BaseSettings` model.
-   Configuration is now loaded via `Config.model_validate(my_dict)` or `Config.from_yaml("path/to/config.yaml")`.

**Old Programmatic Usage:**

```python
# This will no longer work
from temporalloop.config import Config, WorkerConfig

worker_config = WorkerConfig(...)
config = Config(host="...", workers=[worker_config])
```

**New Programmatic Usage:**

```python
from temporalloop.config import Config

config_data = {
    "temporalio": {
        "host": "localhost:7233",
        "workers": [
            {
                "name": "my-worker",
                "queue": "my-queue",
                # ...
            }
        ],
    }
}
config = Config.model_validate(config_data)
```

### 4. Removal of Global Client

The `temporalloop.client` module, including `tclient` and `GTClient`, has been **deleted**. The `Looper` now manages the client instance internally.

**Action Required:** If your code was relying on importing and using `tclient`, you must now create your own `temporalio.client.Client` instance for tasks like starting workflows from external scripts. The client used by workers is handled automatically.

```python
# Old code that will break:
# from temporalloop.client import tclient
# client = await tclient("localhost:7233", "default")

# New approach:
from temporalio.client import Client
client = await Client.connect("localhost:7233", namespace="default")
```
