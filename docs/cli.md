# Command-Line Interface (CLI)

TemporalLoop comes with two command-line tools to simplify worker and schedule management: `temporalloop` and `scheduler`.

## `temporalloop`

The `temporalloop` command is the primary entry point for running your Temporal workers.

### Usage

```bash
temporalloop [OPTIONS]
```

### Options

-   `--config, -c PATH`: The path to your YAML configuration file. This is the recommended way to run `temporalloop`.
-   `--host TEXT`: The address of the Temporal Frontend (e.g., `localhost:7233`). Overrides the value in the config file.
-   `--namespace, -n TEXT`: The Temporal namespace to connect to. Overrides the value in the config file.
-   `--queue, -q TEXT`: The task queue to listen on. This is used for simple, single-worker setups without a config file.
-   `--workflow, -w TEXT`: A workflow to register, in the format `your.module:WorkflowClass`. Can be specified multiple times.
-   `--activity, -a TEXT`: An activity to register, in the format `your.module:activity_func`. Can be specified multiple times.
-   `--interceptor, -i TEXT`: An interceptor class to add, in the format `your.module:InterceptorClass`. Can be specified multiple times.
-   `--log-config PATH`: Path to a logging configuration file (`.ini`, `.json`, or `.yaml`).
-   `--log-level [critical|error|warning|info|debug|trace]`: Sets the log level.
-   `--use-colors / --no-use-colors`: Enable or disable colorized logging output.

### Examples

**Running with a configuration file:**

```bash
temporalloop --config=config.yaml
```

**Overriding configuration with CLI flags:**

```bash
temporalloop --config=config.yaml --host=temporal.prod:7233 --log-level=debug
```

**Running a simple worker without a config file:**

```bash
temporalloop \
  --host=localhost:7233 \
  --namespace=default \
  --queue=my-task-queue \
  --workflow="my_project.workflows:MyWorkflow" \
  --activity="my_project.activities:my_activity"
```

## `scheduler`

The `scheduler` command allows you to synchronize Temporal Schedules based on a YAML definition file.

### Usage

```bash
scheduler [OPTIONS]
```

### Options

-   `--config, -c PATH`: The path to your YAML configuration file, which contains both Temporal connection details and schedule definitions.
-   `--host TEXT`: Overrides the Temporal host from the config file.
-   `--namespace, -n TEXT`: Overrides the Temporal namespace from the config file.

### Example

```bash
scheduler --config=config.yaml
```

This command will connect to the Temporal server defined in `config.yaml` and ensure that the schedules on the server match the definitions found in the `schedules` section of the same file.
