
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
            "workers": [{"name": "worker-1", "queue": "queue-1"}],
        },
        "logging": {"level": "DEBUG"},
    }
    config = Config.model_validate(config_dict)
    assert config.temporalio.host == "remotehost:7233"
    assert config.temporalio.namespace == "production"
    assert config.logging.level == "DEBUG"
    assert len(config.temporalio.workers) == 1
    assert config.temporalio.workers[0].name == "worker-1"
    assert config.temporalio.workers[0].host == "remotehost:7233"


def test_config_from_empty_dict():
    """Test creating Config from an empty dictionary."""
    config = Config.model_validate({})
    assert config.temporalio.host == "127.0.0.1:7233"
    assert config.temporalio.namespace == "default"
    assert config.logging.level == "INFO"
    assert len(config.temporalio.workers) == 0


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
    assert len(config.temporalio.workers) == 1
    assert config.temporalio.workers[0].name == "worker-from-yaml"


def test_worker_settings_inheritance():
    """Test that worker settings inherit from the global temporalio config."""
    config_dict = {
        "temporalio": {
            "host": "global-host",
            "namespace": "global-namespace",
            "workers": [
                {
                    "name": "worker-1",  # Inherits both host and namespace
                    "queue": "queue-1",
                },
                {
                    "name": "worker-2",  # Overrides host, inherits namespace
                    "queue": "queue-2",
                    "host": "worker-host-2",
                },
                {
                    "name": "worker-3",  # Inherits host, overrides namespace
                    "queue": "queue-3",
                    "namespace": "worker-namespace-3",
                },
                {
                    "name": "worker-4",  # Overrides both host and namespace
                    "queue": "queue-4",
                    "host": "worker-host-4",
                    "namespace": "worker-namespace-4",
                },
            ],
        },
    }
    config = Config.model_validate(config_dict)
    assert len(config.temporalio.workers) == 4
    worker1, worker2, worker3, worker4 = config.temporalio.workers

    # Worker 1 should inherit global settings
    assert worker1.host == "global-host"
    assert worker1.namespace == "global-namespace"

    # Worker 2 should use its own host and inherit global namespace
    assert worker2.host == "worker-host-2"
    assert worker2.namespace == "global-namespace"

    # Worker 3 should inherit host and use its own namespace
    assert worker3.host == "global-host"
    assert worker3.namespace == "worker-namespace-3"

    # Worker 4 should use its own host and namespace
    assert worker4.host == "worker-host-4"
    assert worker4.namespace == "worker-namespace-4"
