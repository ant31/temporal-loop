
from temporalloop.config import Config, TemporalInterval, TemporalSchedule
from temporalloop.utils import time_interval


def test_temporal_interval():
    """Test TemporalInterval schema."""
    interval = TemporalInterval(every="1h30m", offset="15s")
    assert interval.every_timedelta() == time_interval("1h30m")
    assert interval.offset_timedelta() == time_interval("15s")


def test_temporal_schedule_schema():
    """Test TemporalSchedule."""
    data = {
        "workflow_id": "test-workflow",
        "workflow": "my_module:MyWorkflow",
        "task_queue": "test-queue",
        "state": "paused",
    }
    schedule = TemporalSchedule(**data)
    assert schedule.workflow_id == "test-workflow"
    assert schedule.state == "paused"


def test_config_from_dict():
    """Test creating Config from a dictionary."""
    config_dict = {
        "temporalio": {
            "host": "remotehost:7233",
            "namespace": "production",
        },
        "workers": [{"name": "worker-1", "queue": "queue-1"}],
        "logging": {"level": "DEBUG"},
    }
    config = Config.model_validate(config_dict)
    assert config.temporalio.host == "remotehost:7233"
    assert config.temporalio.namespace == "production"
    assert config.logging.level == "DEBUG"
    assert len(config.workers) == 1
    assert config.workers[0].name == "worker-1"
    assert config.workers[0].host == "remotehost:7233"


def test_config_from_empty_dict():
    """Test creating Config from an empty dictionary."""
    config = Config.model_validate({})
    assert config.temporalio.host == "127.0.0.1:7233"
    assert config.temporalio.namespace == "default"
    assert config.logging.level == "INFO"
    assert len(config.workers) == 0


def test_config_from_yaml(tmp_path):
    """Test creating Config from a YAML file."""
    yaml_content = """
temporalio:
  host: "yamlhost:7233"
  namespace: "yaml_namespace"
workers:
  - name: "worker-from-yaml"
    queue: "yaml-queue"
logging:
  level: "WARNING"
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = Config.from_yaml(str(config_file))
    assert config.temporalio.host == "yamlhost:7233"
    assert config.temporalio.namespace == "yaml_namespace"
    assert config.logging.level == "WARNING"
    assert len(config.workers) == 1
    assert config.workers[0].name == "worker-from-yaml"
