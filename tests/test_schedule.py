from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.client import Schedule, ScheduleHandle
from temporalio.service import RPCError, RPCStatusCode

from temporalloop.config import TemporalSchedule
from temporalloop.schedule import TemporalScheduler


@pytest.fixture
def mock_client():
    """Fixture for a mocked Temporal client."""
    return MagicMock()


@pytest.fixture
def sample_schedules():
    """Fixture for sample schedule configurations."""
    return {
        "schedule-1": TemporalSchedule.model_validate(
            {
                "workflow_id": "wf-1",
                "workflow": "my_workflows:MyWorkflow",
                "state": "created",
            }
        ),
        "schedule-2": TemporalSchedule.model_validate(
            {
                "workflow_id": "wf-2",
                "workflow": "my_workflows:MyWorkflow",
                "state": "paused",
            }
        ),
        "schedule-3": TemporalSchedule.model_validate(
            {
                "workflow_id": "wf-3",
                "workflow": "my_workflows:MyWorkflow",
                "state": "deleted",
            }
        ),
    }


@pytest.mark.asyncio
@patch("temporalloop.schedule.import_from_string")
async def test_scheduler_prep(mock_import, mock_client, sample_schedules):
    """Test that schedules are prepared correctly."""
    mock_workflow_class = MagicMock()
    mock_workflow_class.run = "run_method"
    mock_import.return_value = mock_workflow_class

    scheduler = TemporalScheduler(mock_client, sample_schedules)
    assert not scheduler.errors
    assert len(scheduler.schedules) == 3
    assert "schedule-1" in scheduler.schedules
    assert scheduler.schedules["schedule-1"].state == "created"
    assert isinstance(scheduler.schedules["schedule-1"].schedule, Schedule)
    assert "schedule-2" in scheduler.schedules
    assert scheduler.schedules["schedule-2"].state == "paused"
    assert "schedule-3" in scheduler.schedules
    assert scheduler.schedules["schedule-3"].state == "deleted"
    assert scheduler.schedules["schedule-3"].schedule is None


@pytest.mark.asyncio
async def test_get_schedule_handle_found(mock_client):
    """Test getting a schedule handle when it exists."""
    scheduler = TemporalScheduler(mock_client, {})
    mock_handle = AsyncMock(spec=ScheduleHandle)
    mock_client.get_schedule_handle.return_value = mock_handle

    handle = await scheduler.get_schedule_handle("exists")
    assert handle is mock_handle
    mock_handle.describe.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_schedule_handle_not_found(mock_client):
    """Test getting a schedule handle when it does not exist."""
    scheduler = TemporalScheduler(mock_client, {})
    mock_handle = AsyncMock(spec=ScheduleHandle)
    rpc_error = RPCError("not found", status=RPCStatusCode.NOT_FOUND, raw_grpc_status=None)
    mock_handle.describe.side_effect = rpc_error
    mock_client.get_schedule_handle.return_value = mock_handle

    handle = await scheduler.get_schedule_handle("not-found")
    assert handle is None


@pytest.mark.asyncio
async def test_sync_schedules(mock_client, sample_schedules):
    """Test the main schedule synchronization logic."""
    scheduler = TemporalScheduler(mock_client, {})

    # Mock the individual action methods
    scheduler.created_schedule = AsyncMock()
    scheduler.paused_schedule = AsyncMock()
    scheduler.deleted_schedule = AsyncMock()

    # Re-prep with mocks
    scheduler.schedules = {}
    scheduler.errors = []
    with patch("temporalloop.schedule.import_from_string"):
        scheduler.prep_schedules(sample_schedules)

    await scheduler.sync_schedules()

    scheduler.created_schedule.assert_awaited_once()
    scheduler.paused_schedule.assert_awaited_once()
    scheduler.deleted_schedule.assert_awaited_once()


@pytest.mark.asyncio
@patch("temporalloop.schedule.import_from_string")
async def test_scheduler_prep_with_import_error(mock_import, mock_client, sample_schedules):
    """Test that schedule prep is fault-tolerant to import errors."""
    # Add an invalid schedule
    sample_schedules["invalid-schedule"] = TemporalSchedule.model_validate(
        {
            "workflow_id": "wf-invalid",
            "workflow": "non_existent:Workflow",
        }
    )
    # Make the import fail for the invalid one
    from temporalloop.importer import ImportFromStringError

    def side_effect(name):
        if "non_existent" in name:
            raise ImportFromStringError(f"Could not import module {name}")
        mock_wf = MagicMock()
        mock_wf.run = "run"
        return mock_wf

    mock_import.side_effect = side_effect

    scheduler = TemporalScheduler(mock_client, sample_schedules)

    # Check that the error was recorded but other schedules were processed
    assert len(scheduler.errors) == 1
    assert "Failed to prepare schedule 'invalid-schedule'" in str(scheduler.errors[0])
    assert len(scheduler.schedules) == 3  # The 3 valid ones
    assert "invalid-schedule" not in scheduler.schedules

    # Check that sync_schedules raises an exception
    with pytest.raises(RuntimeError, match="Aborting sync due to preparation errors"):
        await scheduler.sync_schedules()
