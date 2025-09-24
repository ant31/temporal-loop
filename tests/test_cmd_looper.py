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
    assert len(config_arg.workers) == 1
    worker = config_arg.workers[0]
    assert worker.queue == "testq"
    assert worker.workflows == ["my.workflow:W"]
    assert worker.activities == ["my.activity:a"]


