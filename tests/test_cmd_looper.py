from unittest.mock import patch

from typer.testing import CliRunner

from temporalloop.cmd.looper import app

runner = CliRunner()


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_with_config(mock_run, tmp_path):
    """Test the looper CLI with a config file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: "localhost:7233"
"""
    )
    result = runner.invoke(app, ["--config", str(config_file)])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.host == "localhost:7233"


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_with_config_and_overrides(mock_run, tmp_path):
    """Test that CLI arguments override config file settings."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: "config-host:7233"
  namespace: "config-namespace"
"""
    )
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
            "--host",
            "cli-host:1234",
            "--namespace",
            "cli-namespace",
        ],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.host == "cli-host:1234"
    assert config_arg.temporalio.namespace == "cli-namespace"


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_namespace_override_propagates_to_workers(mock_run, tmp_path):
    """Test that the --namespace CLI override is propagated to workers."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: "config-host:7233"
  namespace: "config-namespace"
  workers:
    - name: "worker-1"
      queue: "queue-1"
"""
    )
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
            "--namespace",
            "cli-namespace",
        ],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.namespace == "cli-namespace"
    assert len(config_arg.temporalio.workers) == 1
    worker = config_arg.temporalio.workers[0]
    assert worker.namespace == "cli-namespace"


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_without_namespace_override(mock_run, tmp_path):
    """Test that without --namespace override, the config namespace is used."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: "config-host:7233"
  namespace: "config-namespace"
  workers:
    - name: "worker-1"
      queue: "queue-1"
"""
    )
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
        ],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.namespace == "config-namespace"
    assert len(config_arg.temporalio.workers) == 1
    worker = config_arg.temporalio.workers[0]
    assert worker.namespace == "config-namespace"


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_worker_namespace_inheritance(mock_run, tmp_path):
    """Test worker-level namespace overrides from config without CLI interaction."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: "config-host:7233"
  namespace: "global-namespace"
  workers:
    - name: "worker-1" # Inherits global namespace
      queue: "queue-1"
    - name: "worker-2" # Overrides namespace
      queue: "queue-2"
      namespace: "worker-2-namespace"
"""
    )
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
        ],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.namespace == "global-namespace"
    assert len(config_arg.temporalio.workers) == 2
    worker1, worker2 = config_arg.temporalio.workers
    assert worker1.namespace == "global-namespace"
    assert worker2.namespace == "worker-2-namespace"


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_config_namespace_without_overrides(mock_run, tmp_path):
    """Test that the namespace from the config file is used when no CLI overrides are given."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: "config-host:7233"
  namespace: "toto"
  workers:
    - name: "worker-1"
      queue: "queue-1"
"""
    )
    result = runner.invoke(
        app,
        [
            "--config",
            str(config_file),
        ],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.namespace == "toto"
    assert len(config_arg.temporalio.workers) == 1
    worker = config_arg.temporalio.workers[0]
    assert worker.namespace == "toto"


@patch("temporalloop.cmd.looper.run")
def test_looper_cli_with_args(mock_run):
    """Test the looper CLI with command-line arguments."""
    result = runner.invoke(
        app,
        [
            "--host",
            "testhost:1234",
            "--namespace",
            "testns",
            "--queue",
            "testq",
            "--workflow",
            "my.workflow:W",
            "--activity",
            "my.activity:a",
        ],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once()
    config_arg = mock_run.call_args[0][0]
    assert config_arg.temporalio.host == "testhost:1234"
    assert config_arg.temporalio.namespace == "testns"
    assert len(config_arg.temporalio.workers) == 1
    worker = config_arg.temporalio.workers[0]
    assert worker.queue == "testq"
    assert worker.workflows == ["my.workflow:W"]
    assert worker.activities == ["my.activity:a"]


