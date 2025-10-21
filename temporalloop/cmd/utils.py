from pathlib import Path

from temporalloop.config import Config


def load_config_with_overrides(config_path: Path, host: str | None, namespace: str | None) -> Config:
    """Load a Config object from a YAML file and apply CLI overrides.

    Args:
        config_path: Path to the YAML configuration file.
        host: The Temporal host to override the config with.
        namespace: The Temporal namespace to override the config with.

    Returns:
        The loaded and updated Config object.
    """
    config = Config.from_yaml(str(config_path))
    if host is not None:
        config.temporalio.host = host
    if namespace is not None:
        config.temporalio.namespace = namespace

    # Manually re-apply the inheritance to propagate the new host and namespace to workers
    config.temporalio.inherit_worker_settings()
    return config
