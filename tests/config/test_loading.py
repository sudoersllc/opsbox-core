from unittest.mock import patch

from opsbox.config import AppConfig

# ruff: noqa: S101


@patch("os.sys.argv", ["script_name"])
@patch.dict("os.environ", {"opa_upload_url": "http://env-url", "modules": "test_plugin_1-test_plugin_4"}, clear=True)
def test_grab_args_with_env():
    """Test grabbing arguments from environment variables."""
    app_config = AppConfig()
    conf, pipeline = app_config._grab_args()
    assert conf["opa_upload_url"] == "http://env-url"


def test_singleton_behavior():
    """Test the singleton behavior of the AppConfig class."""
    app_config1 = AppConfig()
    app_config2 = AppConfig()
    assert app_config1 is app_config2  # Should be the same instance
