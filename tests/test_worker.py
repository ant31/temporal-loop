from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.client import Client
from temporalio.worker import Worker
from temporalloop.config import Config
from temporalloop.worker import Looper, WorkerFactory


@pytest.fixture
def mock_config():
    """Returns a mock Config object."""
    config_data = {
        "temporalio": {
            "host": "localhost:7233",
            "namespace": "default",
            "workers": [
                {
                    "name": "test-worker",
                    "queue": "test-queue",
                    "workflows": [],
                    "activities": [],
                }
            ],
        }
    }
    config = Config.model_validate(config_data)
    return config


@pytest.mark.asyncio
async def test_worker_factory_client_creation(mock_config):
    """Test WorkerFactory client creation."""
    factory = WorkerFactory(mock_config)
    with patch("temporalio.client.Client.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = "new_client"
        client = await factory.client(mock_config.temporalio)
        mock_connect.assert_awaited_with("localhost:7233", namespace="default")
        assert client == "new_client"


@pytest.mark.asyncio
async def test_worker_factory_new_worker(mock_config):
    """Test WorkerFactory new_worker creation."""
    mock_client = MagicMock(spec=Client)
    factory = WorkerFactory(mock_config)
    worker_config = mock_config.temporalio.workers[0]

    with patch("temporalloop.worker.Worker", spec=Worker) as mock_worker_class:
        worker_instance = await factory.new_worker(
            worker_config,
            mock_client,
            loaded_workflows=[],
            loaded_activities=[],
            loaded_interceptors=[],
            loaded_pre_init=[],
        )
        mock_worker_class.assert_called_once()
        assert worker_instance is mock_worker_class.return_value


@pytest.mark.asyncio
async def test_looper_prepare_workers(mock_config):
    """Test Looper worker preparation."""
    looper = Looper(mock_config)
    with patch("temporalloop.worker.WorkerFactory.new_worker", new_callable=AsyncMock) as mock_new_worker, patch(
        "temporalloop.worker.WorkerFactory.client", new_callable=AsyncMock
    ) as mock_client:
        mock_new_worker.return_value = MagicMock(spec=Worker)
        mock_client.return_value = MagicMock(spec=Client)

        workers = await looper.prepare_workers()

        assert len(workers) == 1
        mock_new_worker.assert_awaited_once()


@pytest.mark.asyncio
async def test_looper_run(mock_config):
    """Test the main run loop of the Looper."""
    looper = Looper(mock_config)
    mock_worker = MagicMock(spec=Worker)
    mock_worker.run = AsyncMock()

    with patch.object(looper, "prepare_workers", new_callable=AsyncMock) as mock_prepare, patch.object(
        looper, "install_signal_handlers"
    ) as mock_signals, patch("temporalloop.config.Config.configure_logging") as mock_logging:
        mock_prepare.return_value = [mock_worker]

        await looper.run()

        mock_signals.assert_called_once()
        mock_logging.assert_called_once()
        mock_prepare.assert_awaited_once()
        mock_worker.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_looper_stop(mock_config):
    """Test the stop functionality of the Looper."""
    looper = Looper(mock_config)
    mock_worker = MagicMock(spec=Worker)
    mock_worker.shutdown = AsyncMock()
    looper.workers = [mock_worker]
    looper.client = MagicMock(spec=Client)
    looper.client.close = AsyncMock()

    await looper.stop()

    mock_worker.shutdown.assert_awaited_once()
    looper.client.close.assert_awaited_once()


def test_handle_exit_sigterm():
    """Test that handle_exit raises SystemExit for SIGTERM."""
    looper = Looper(MagicMock())
    with pytest.raises(SystemExit):
        looper.handle_exit(15, None)  # SIGTERM


def test_handle_exit_sigint():
    """Test that handle_exit raises SystemExit for SIGINT."""
    looper = Looper(MagicMock())
    with pytest.raises(SystemExit):
        looper.handle_exit(2, None)  # SIGINT
