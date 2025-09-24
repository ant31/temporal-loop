# Managing Schedules

TemporalLoop provides a command-line tool, `scheduler`, to help you manage [Temporal Schedules](https://docs.temporal.io/schedules) in a declarative way. Instead of creating and updating schedules programmatically, you can define them in a YAML file and use the `scheduler` to synchronize them with your Temporal server.

## 1. Define Schedules in Your `config.yaml`

Schedules are defined directly within your main `config.yaml` file under a top-level `schedules` key. Each key under `schedules` is a unique ID for your schedule.

```yaml
# config.yaml
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"
  # ... other worker settings ...

schedules:
  my-hourly-workflow:
    # The workflow ID that will be used for each run.
    workflow_id: "my-workflow-id-001"
    # Import string for the workflow to run.
    workflow: "my_project.workflows:GreetingWorkflow"
    # Task queue for the workflow executions.
    task_queue: "greeting-queue"
    # The schedule interval.
    interval:
      every: "1h" # e.g., "1h30m15s"
      offset: "15m" # Optional
    # A Pydantic model for the workflow input.
    input_schema: "my_project.schemas:GreetingInput"
    # The payload (input) for the workflow.
    payload:
      name: "Scheduled Workflow"
    # State can be "created", "paused", or "deleted".
    state: "created"
    # An optional comment for the schedule.
    comment: "Runs the greeting workflow every hour."

  another-paused-schedule:
    workflow_id: "another-workflow-002"
    workflow: "my_project.workflows:AnotherWorkflow"
    task_queue: "another-queue"
    interval:
      every: "24h"
    payload: {}
    state: "paused"
```

## 2. Synchronize Schedules

Run the `scheduler` command, pointing it to your `config.yaml`.

```bash
scheduler --config=config.yaml
```

### How Synchronization Works

The `scheduler` tool performs the following actions for each schedule defined in the `schedules` section of your config file:

-   **If `state` is `created`**:
    -   If the schedule does not exist on the server, it will be created.
    -   If the schedule already exists, it will be updated to match the configuration in the file.
-   **If `state` is `paused`**:
    -   If the schedule exists, it will be paused.
    -   If it doesn't exist, it will be created in a paused state.
-   **If `state` is `deleted`**:
    -   If the schedule exists, it will be deleted from the server.
    -   If it doesn't exist, no action is taken.

This declarative approach makes it easy to manage your schedules as part of your application's source code and deployment process.
