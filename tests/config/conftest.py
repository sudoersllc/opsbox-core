import pytest
from opsbox.config import AppConfig


@pytest.fixture
def appconfig():
    """dummy fixture for the AppConfig class."""
    config = AppConfig()
    yield config
    config._instance = None
