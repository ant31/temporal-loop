# TemporalLoop Improvement Plan

This document outlines the major epics and tasks required to improve the `temporalloop` project to a production-grade level, targeting a score of at least 18/20 (an average of 9/10 across all categories).

---

## Epic 1: Overhaul Configuration Management (DONE)

**Goal:** Refactor the entire configuration system to be simple, robust, and maintainable. This will resolve the current architecture's primary weakness.

**Target Categories:** Architecture, Maintainability, Code Quality

### Tasks:
-   [x] **Consolidate Configuration Models:**
    -   Merge `config.py` and `config_loader.py` into a single, authoritative `temporalloop/config.py`.
    -   Eliminate the `Config` and `WorkerConfig` classes in favor of a single, nested Pydantic `Settings` model. This model will be the single source of truth for configuration.
    -   The new model should cleanly handle loading from a YAML file, environment variables, and CLI arguments.

-   [x] **Simplify Worker Configuration Inheritance:**
    -   Remove the `_merge` method from `WorkerConfig`.
    -   Implement a system where worker-specific settings transparently inherit from global settings during the Pydantic model's construction. This should be done declaratively within the model itself.

-   [x] **Improve Programmatic Usage:**
    -   Remove all `sys.exit(1)` calls from the configuration loading and importer logic. All errors should be raised as specific exceptions (e.g., `ConfigurationError`), allowing programmatic users to handle them gracefully.

-   [x] **Refactor CLI:**
    -   Update the CLI commands in `temporalloop/cmd/` to use the new, simplified configuration model.

---

## Epic 2: Implement a Comprehensive Test Suite (IN PROGRESS)

**Goal:** Achieve >90% test coverage and build a robust suite of unit and integration tests to guarantee reliability and stability.

**Target Categories:** Testing, Maturity, Code Quality

### Tasks:
-   [x] **Expand Unit Test Coverage:**
    -   Write comprehensive unit tests for the core logic in `temporalloop/worker.py`, including the `Looper`'s lifecycle (startup, shutdown) and the `WorkerFactory`.
    -   Write unit tests for the new configuration system, covering all loading scenarios (YAML, env vars, defaults).
    -   Write unit tests for all CLI commands, mocking external dependencies and verifying inputs and outputs.

-   [ ] **Develop an Integration Test Suite:**
    -   Set up testing infrastructure to run a Temporal development server during the test suite execution (e.g., via Docker or `temporal-cli`).
    -   Create integration tests that:
        -   Load a sample `config.yaml`.
        -   Start the `Looper` with a real worker.
        -   Execute a test workflow/activity against the live test server and verify the result.
        -   Test the graceful shutdown signal handling.
        -   Verify the `scheduler` command can successfully create, update, pause, and delete a schedule on the server.

---

## Epic 3: Enhance Documentation to Professional Standards (DONE)

**Goal:** Create clear, comprehensive, and professional documentation that empowers new users and aids contributors.

**Target Categories:** Documentation

### Tasks:
-   [x] **Generate an API Reference:**
    -   Integrate `mkdocstrings` into the `mkdocs` build process.
    -   Create an "API Reference" section in the documentation that automatically generates documentation from the codebase's docstrings.

-   [x] **Improve Docstrings:**
    -   Review and rewrite all public-facing docstrings for modules, classes, and functions to be clear, complete, and follow the Google Python Style Guide.

-   [x] **Expand User Guides:**
    -   Create an "Advanced Usage" guide covering topics like creating a custom `WorkerFactory` and best practices for embedding `temporalloop` in a larger application.
    -   Add more complex examples to the `schedules.md` documentation.
    -   Create a "Cookbook" section with complete, runnable examples for common patterns (e.g., setting up advanced interceptors, multi-queue setups).

---

## Epic 4: Refine Code Quality and Remove Technical Debt (IN PROGRESS)

**Goal:** Address all identified code smells and weaknesses to improve the long-term health and maintainability of the codebase.

**Target Categories:** Code Quality, Maintainability

### Tasks:
-   [x] **Refactor `WorkerConfig`:**
    -   As part of the configuration overhaul (Epic 1), break down the monolithic `WorkerConfig` into smaller, more focused Pydantic models to eliminate the "too many arguments" code smell.
    -   Ensure no mutable default arguments (`[]` or `{}`) are used in function signatures or Pydantic model fields; use `default_factory` instead.

-   [x] **Eliminate Global State:**
    -   Refactor the `GTClient` singleton into a dependency that can be explicitly managed and injected. This will improve testability and make the client's lifecycle explicit. The `Looper` could be responsible for creating and managing a single client instance to be shared among workers. (DONE by removing unused `TClient` module).

-   [x] **Enforce Stricter Linting:**
    -   Review and remove all `pylint: disable` comments. The code should be refactored to comply with the linter rules.
    -   Configure `ruff` to be stricter to catch more potential issues. (IN PROGRESS: Enabled `flake8-annotations`).

---

## Epic 5: Harden for Production Use

**Goal:** Address architectural weaknesses to improve robustness, fault tolerance, and developer experience in production environments.

**Target Categories:** Architecture, Maturity, Code Quality

### Tasks:
1.  **Decouple Configuration and Code Loading:**
    -   Refactor the `Config` model to separate data validation from the side effect of dynamically importing callables. The loading of workflows/activities should happen in the `Looper` or `WorkerFactory`, not during configuration parsing. This allows the config to be used in more contexts (e.g., validation scripts, UIs) without triggering imports.

2.  **Improve Error Handling in Scheduler:**
    -   Refactor `TemporalScheduler` to be more fault-tolerant. A failure to load one workflow/schema from an import string should not prevent the synchronization of other, valid schedules. The tool should attempt to process all schedules and report a collection of errors at the end.

3.  **Integrate Schedule Management:**
    -   Make `schedules` a top-level key in `config.yaml`, on par with `workers`.
    -   Update the `scheduler` CLI to read this key by default, removing the need for a separate `--schedules-file` and making schedule management a first-class, fully integrated feature.

4.  **Refactor CLI Argument Parsing:**
    -   Create a shared utility function or Typer context to handle the common logic of loading a base `config.yaml` and overriding specific fields (like `host` and `namespace`) from CLI flags. This will reduce code duplication between `cmd/looper.py` and `cmd/scheduler.py`.
