from unittest.mock import patch

import pytest

from opsbox.config import AppConfig
import json
from datetime import datetime

# ruff: noqa: S101

json_file = "tests/test_config.json"

@patch("os.sys.argv", ["script_name"])
@patch.dict("os.environ", {"opa_upload_url": "http://env-url", "modules": "test_plugin_1-test_plugin_4"}, clear=True)
def test_grab_args_with_env(app_config):
    """Test grabbing arguments from environment variables."""
    conf, pipeline = app_config._grab_args()
    assert conf["opa_upload_url"] == "http://env-url"


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4"])
def test_grab_args_with_argv(app_config):
    """Test grabbing arguments from command line arguments."""
    conf, pipeline = app_config._grab_args()
    assert conf["modules"] == "test_plugin_1-test_plugin_4"


@patch("os.sys.argv", ["script_name", "--config", json_file])
def test_grab_args_with_json_file(app_config):
    """Test grabbing arguments from a JSON file."""
    # Make a temporary JSON file from a dictionary
    out_dict = {"modules": "test_plugin_1-test_plugin_4", "test1": "test_value", "test2": "test_value", "test3": "test_value"}
    with open(json_file, "w") as f:
        json.dump(out_dict, f)
    
    conf, pipeline = app_config._grab_args()
    assert conf["modules"] == "test_plugin_1-test_plugin_4"

@patch("os.sys.argv", ["script_name", "--config", "fake_file.json"])
def test_grab_args_with_fake_json_file(app_config):
    """Test grabbing arguments from a non-existent JSON file."""
    with pytest.raises(FileNotFoundError):
        conf, pipeline = app_config._grab_args()

@patch("os.sys.argv", ["script_name","--config", json_file])
def test_grab_args_with_malformed_json_file(app_config):
    """Test grabbing arguments from a JSON file with no modules."""
    # Make a temporary JSON file from a dictionary
    out_dict = {"test1": "test_value", "test2": "test_value", "test3": "test_value"}
    with open(json_file, "w") as f:
        json.dump(out_dict, f)

    # Make sure that it can't be loaded (trigger json decode error)
    with open(json_file, "a") as f:
        f.write("}")
    
    with pytest.raises(json.decoder.JSONDecodeError):
        conf, pipeline = app_config._grab_args()

@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--date=2021-01-01", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value"])
def test_grab_date_args(app_config):
    """Test grabbing date arguments."""

    conf, pipeline = app_config._grab_args()
    date_obj = conf.get("date")
    assert date_obj == datetime(2021, 1, 1)

@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--date=2021-01-01", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value", "--oai_key=1234"])

def test_singleton_behavior():
    """Test the singleton behavior of the AppConfig class."""
    app_config1 = AppConfig()
    app_config2 = AppConfig()
    assert app_config1 is app_config2  # Should be the same instance
    AppConfig._instance = None  # Reset the singleton
