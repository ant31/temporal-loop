# Welcome to TemporalLoop

TemporalLoop is a Python framework designed to simplify the process of running and managing [Temporal.io](https://temporal.io) workers. Inspired by the simplicity of Uvicorn for ASGI applications, TemporalLoop allows you to define and configure multiple workers with their respective activities, workflows, and settings using a straightforward configuration file. This approach aims to minimize boilerplate code, streamline worker management, and enhance interoperability within Temporal-based microservices.

## Key Features

- **Declarative Configuration**: Configure workers, workflows, and activities in a single YAML file.
- **Multiple Workers**: Run and manage multiple workers in a single process.
- **Customizable**: Easily extend with custom data converters, interceptors, and worker factories.
- **Graceful Shutdown**: Handles signals for a clean shutdown.
- **Scheduler Management**: Command-line tool for managing Temporal Schedules.

## User Guide

- **[Getting Started](./getting-started.md)**: A step-by-step tutorial to get your first worker running.
- **[Configuration](./configuration.md)**: A detailed reference for all configuration options.
- **[Command-Line Interface (CLI)](./cli.md)**: Learn how to use the `temporalloop` and `scheduler` commands.
- **[Programmatic Usage](./programmatic-usage.md)**: Integrate TemporalLoop into your Python applications.
- **[Managing Schedules](./schedules.md)**: How to define and manage Temporal Schedules.

## For Contributors

- **[Core Concepts](./core-concepts.md)**: Understand the internal architecture of TemporalLoop.
- **[Contributing](./contributing.md)**: Guidelines for contributing to the project.
