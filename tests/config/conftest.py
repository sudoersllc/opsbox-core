import pytest
from opsbox.config import AppConfig
from opsbox.plugins import Registry


@pytest.fixture
def app_config():
    """dummy fixture for the AppConfig class."""
    # Nuke the singleton instance
    AppConfig._instances = {}
    Registry._instances = {}

    # Create a new AppConfig instance and return it
    config = AppConfig()
    yield config

    # Nuke the singleton instances
    config._instances = {}
    Registry._instances = {}


