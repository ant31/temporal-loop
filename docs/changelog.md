# Changelog

## Version 0.4.0

### ✨ New Features & Improvements

-   **Complete Configuration Overhaul**: The entire configuration system has been rebuilt using Pydantic for a more robust, declarative, and type-safe experience. Configuration is now managed through a single, nested `Config` object.
-   **Simplified Worker Configuration**: Worker-specific settings now automatically inherit from the global `temporalio` configuration block, reducing duplication.
-   **Improved CLI**: The command-line interfaces for both `temporalloop` and `scheduler` have been migrated from `click` to `typer`, providing better type hinting, auto-completion, and a cleaner implementation.
-   **Integrated Schedule Management**: The `scheduler` command now reads schedule definitions directly from the main `config.yaml` under the `schedules` key, making it a first-class, integrated feature.
-   **Enhanced Programmatic API**: The new configuration system makes it much easier and cleaner to configure and run TemporalLoop from within your own Python code.
-   **Fault-Tolerant Scheduler**: The scheduler is now more robust. A failure to load one workflow or schema will not prevent the synchronization of other valid schedules. A summary of errors is provided at the end.
-   **Removed Global Client**: The internal global `TClient` singleton has been removed, improving testability and making the client's lifecycle explicit and managed by the `Looper`.
