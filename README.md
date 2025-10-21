# TemporalLoop

TemporalLoop is a Python framework designed to simplify the process of running and managing [Temporal.io](https://temporal.io) workers. Inspired by the simplicity of Uvicorn, it allows you to define and configure multiple workers using a straightforward YAML configuration file.

## Key Features

-   **Declarative Configuration**: Define workers, workflows, and settings in a single YAML file.
-   **Multi-Worker Support**: Run and manage multiple workers from a single process.
-   **Extensible**: Easily customize with your own data converters, interceptors, and worker factories.
-   **CLI and Programmatic API**: Use the simple command-line interface or integrate it into your application.
-   **Scheduler Management**: A command-line tool to declaratively manage Temporal Schedules.

## Documentation

For full documentation, including a getting started guide, configuration reference, and contributing guidelines, please see the **[docs](./docs/index.md)** directory.

## Quick Start

### 1. Installation

```bash
pip install temporalloop
```

### 2. Configuration

Create a `config.yaml` to define your workers:

```yaml
# config.yaml
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"

workers:
  - name: "my-worker"
    queue: "my-task-queue"
    workflows:
      - "my_project.workflows:MyWorkflow"
    activities:
      - "my_project.activities:my_activity"
```

### 3. Run

Start your workers with the `temporalloop` command:

```bash
temporalloop --config=config.yaml
```

## Contributing

Contributions are welcome! Please see the **[Contributing Guide](./docs/contributing.md)** for details on how to set up your development environment and submit pull requests.

## License

This project is licensed under the terms of the `LICENSE` file.


