# Contributing to TemporalLoop

We welcome contributions from the community! Whether you're fixing a bug, adding a new feature, or improving documentation, your help is appreciated.

## Development Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/temporalloop.git
    cd temporalloop
    ```

2.  **Set up a virtual environment:**

    We recommend using a virtual environment to manage dependencies.

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**

    The project uses `uv` for package management.

    ```bash
    uv pip install -e ".[dev]"
    ```

4.  **Set up pre-commit hooks:**

    This project uses `pre-commit` to automatically run linters and formatters before each commit.

    ```bash
    pre-commit install
    ```

## Running Tests

To run the test suite, use the `make` command:

```bash
make test
```

This will run `pytest` and generate a coverage report.

## Code Style and Linting

We use the following tools to maintain code quality:

-   **`black`** for code formatting.
-   **`ruff`** for linting.
-   **`isort`** for sorting imports.

These tools are automatically run by the pre-commit hooks, but you can also run them manually:

```bash
make lint
```

## Submitting a Pull Request

1.  Create a fork of the repository and create a new branch for your changes.
2.  Make your changes, ensuring that all tests pass and the code is properly linted.
3.  Add or update documentation as needed.
4.  Write a clear and concise commit message.
5.  Push your changes to your fork and open a pull request against the `main` branch of the original repository.

## Project Structure

-   `temporalloop/`: The main source code for the library.
    -   `cmd/`: Code for the command-line interfaces (`looper.py`, `scheduler.py`).
    -   `converters/`: Custom data converters.
    -   `interceptors/`: Worker interceptors.
    -   `config.py`: The `Config` and `WorkerConfig` classes.
    -   `worker.py`: The core `Looper` and `WorkerFactory` logic.
-   `tests/`: Unit tests for the project.
-   `docs/`: Documentation files.
-   `config.yaml`: An example configuration file.
-   `pyproject.toml`: Project metadata and dependency definitions.
