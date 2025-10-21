# Core Concepts

This document explains the key components of TemporalLoop and how they work together. Understanding these concepts is helpful for advanced usage and for contributing to the project.

## `Config` and Pydantic Models

-   **`Config`**: This Pydantic `BaseSettings` class (`temporalloop.config.Config`) is the main container for the entire configuration. It nests other models like `TemporalSettings`, `WorkerSettings`, and `LoggingSettings`.
-   **Declarative Inheritance**: When the `Config` model is validated (either from a YAML file or a dictionary), it automatically handles the inheritance of settings from the global `temporalio` section down to each individual worker in the `workers` list. For example, if a worker does not define a `host`, it inherits the one from the global section.
-   **Dynamic Loading**: During validation, the model also takes care of dynamically importing all callables specified as strings (workflows, activities, interceptors, etc.) and stores them in `loaded_*` fields on the `WorkerSettings` instances, ready to be used by the `Looper`.

## `Looper`

The `Looper` class (`temporalloop.worker.Looper`) is the engine that runs the workers. Its primary responsibilities are:

1.  **Initialization**: It takes a `Config` object upon initialization.
2.  **Signal Handling**: It sets up handlers for `SIGINT` and `SIGTERM` to ensure a graceful shutdown.
3.  **Worker Preparation**: It iterates through the `WorkerSettings` objects in `config.temporalio.workers`, uses the loaded factory (`worker.loaded_factory`) to create a `temporalio.worker.Worker` instance for each one.
4.  **Running Workers**: It runs all the created worker instances concurrently using `asyncio.gather`.
5.  **Shutdown**: When a shutdown signal is received, it calls the `shutdown()` method on each worker.

## `WorkerFactory`

The `WorkerFactory` class (`temporalloop.worker.WorkerFactory`) is responsible for creating `temporalio.worker.Worker` instances. The default implementation does the following:

1.  **Creates a Temporal Client**: It establishes a connection to the Temporal server using the settings from the `WorkerConfig`.
2.  **Instantiates the Worker**: It creates a `Worker` object, passing the client, task queue, workflows, activities, interceptors, and other settings.

You can create a custom `WorkerFactory` by subclassing it and overriding its methods. This allows you to customize client creation or worker instantiation, for example, to add custom telemetry or metrics. You can specify your custom factory in `config.yaml` using the `factory` option.

## Importers and String-based Configuration

TemporalLoop heavily relies on import strings (e.g., `"my_project.workflows:MyWorkflow"`) in its configuration. This is handled by the `import_from_string` utility (`temporalloop.importer.import_from_string`). This function dynamically imports modules and retrieves attributes, allowing for a fully declarative configuration without needing to import all your workflows and activities into your main script.

## Data Converters and Interceptors

-   **Data Converters**: TemporalLoop allows you to specify a global or per-worker `DataConverter`. It provides a `pydantic_data_converter` (`temporalloop.converters.pydantic`) out of the box, which uses Pydantic for JSON serialization. This makes it easy to use Pydantic models as inputs and outputs for your workflows and activities.

-   **Interceptors**: You can add interceptors globally or to specific workers. These are powerful tools for implementing cross-cutting concerns like logging, metrics, or error reporting. TemporalLoop includes a `SentryInterceptor` (`temporalloop.interceptors.sentry`) for reporting exceptions to Sentry.
