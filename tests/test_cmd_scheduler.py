from unittest.mock import patch

from typer.testing import CliRunner

from temporalloop.cmd.scheduler import app

runner = CliRunner()


@patch("asyncio.run")
def test_scheduler_cli(mock_asyncio_run, tmp_path):
    """Test the scheduler CLI command."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
temporalio:
  host: 'localhost:7233'
schedules:
  my-schedule:
    workflow_id: "wf-1"
    workflow: "my.workflow:W"
"""
    )

    with patch("temporalloop.cmd.scheduler.run") as mock_run_coro:
        result = runner.invoke(app, ["--config", str(config_file)])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

        # Check that the config was created and passed correctly to the coroutine
        mock_run_coro.assert_called_once()
        config_arg = mock_run_coro.call_args[0][0]
        assert config_arg.temporalio.host == "localhost:7233"
        assert "my-schedule" in config_arg.schedules
        assert config_arg.schedules["my-schedule"].workflow_id == "wf-1"
