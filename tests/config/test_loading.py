from unittest.mock import patch

import pytest

# ruff: noqa: S101


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--plugin_dir", "tests/test_plugins", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value"])
def test_load_correctly(app_config):
    """Test loading from command line arguments."""
    app_config.load()
    assert app_config.basic_settings.modules == ["test_plugin_1", "test_plugin_4"]
    assert app_config.module_settings["test1"] == "test_value"
    assert app_config.module_settings["test2"] == "test_value"
    assert app_config.module_settings["test3"] == "test_value"


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--plugin_dir", "tests/test_plugins"])
def test_load_missing_args(app_config):
    """Test loading from command line arguments with missing args."""
    result = app_config.load()
    assert len(result) == 2


@patch("os.sys.argv", ["script_name", "--plugin_dir", "tests/test_plugins"])
def test_load_missing_modules(app_config):
    """Test loading from command line arguments with missing args."""
    with pytest.raises(ValueError):
        app_config.load()


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--plugin_dir", "tests/test_plugins", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value"])
def test_grab_env_plugins(app_config):
    """Test grabbing plugins from environment variables."""
    results = app_config.grab_conf_environment_plugins()
    assert len(results) == 8


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--plugin_dir", "tests/test_plugins", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value"])
def test_caching(app_config):
    """Test caching."""
    app_config.load()
    app_config.init_settings()
    assert all([hasattr(app_config, "basic_settings"), hasattr(app_config, "module_settings")])


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value", "--oai_key=sk876861234"])
def test_LLM_conf(app_config):
    """Test grabbing LLM configuration."""
    app_config.init_settings()
    app_config.init_llms()
    assert app_config.llm_settings.oai_key == "sk876861234"
    assert app_config.llm is not None


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--test1", "test_value", "--test2", "test_value", "--test3", "test_value", "--plugin_dir", "tests/test_plugins"])
def test_load_all_fields(app_config):
    """Test loading all fields."""
    results = app_config.load(all_fields=True)
    assert len(results) == 2


@patch("os.sys.argv", ["script_name", "--modules", "test_plugin_1-test_plugin_4", "--plugin_dir", "tests/test_plugins", "--help"])
def test_help(app_config):
    """Test help."""
    results = app_config.load()
    assert len(results) == 2
