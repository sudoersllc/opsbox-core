import pytest
from unittest.mock import patch
from opsbox.cli import (
    print_welcome_message,
    print_pipeline_building_help,
    print_plugin_not_found_error,
    print_config_help,
    print_available_plugins,
    print_pipeline_help,
    print_basic_args_help,
    print_missing_arguments_error,
)
from rich.console import Console
from io import StringIO

# ruff: noqa: S101


@pytest.fixture
def mock_console():
    """Mock the rich console object for capturing output."""
    with patch("opsbox.cli.console", new=Console(file=StringIO(), force_terminal=True)) as mock_console:
        yield mock_console


def test_print_welcome_message(mock_console):
    """Test the welcome message."""
    print_welcome_message()
    output = mock_console.file.getvalue()
    assert "Welcome to Opsbox" in output


def test_print_pipeline_building_help(mock_console):
    """Test the pipeline building help message."""
    print_pipeline_building_help()
    output = mock_console.file.getvalue()
    assert "Opsbox uses a series of modules" in output


def test_print_plugin_not_found_error(mock_console):
    """Test the plugin not found error message."""
    print_plugin_not_found_error("some/path", Exception("Test error"))
    output = mock_console.file.getvalue()
    assert "plugin_dir some/path" in output
    assert "Test error" in output


def test_print_config_help(mock_console):
    """Test the config help message."""
    print_config_help()
    output = mock_console.file.getvalue()
    assert "Opsbox can be configured through either" in output


def test_print_available_plugins(mock_console):
    """Test the available plugins message."""
    plugins = [("plugin1", "type1"), ("plugin2", "type2")]
    print_available_plugins(plugins, plugin_dir="/test/plugins")
    output = mock_console.file.getvalue()
    assert "plugin1" in output
    assert "plugin2" in output
    assert "/test/plugins" in output


def test_print_pipeline_help(mock_console):
    """Test the pipeline help message."""

    class MockFieldInfo:
        description = "desc"

        @staticmethod
        def is_required():
            return True

    modules = ["module1", "module2"]
    models = [("arg1", "plugin1", MockFieldInfo())]

    print_pipeline_help(modules, models)
    output = mock_console.file.getvalue()
    assert "Viewing the help for the following pipeline" in output
    assert "module1-module2" in output
    assert "plugin1" in output


def test_print_basic_args_help(mock_console):
    """Test the basic args help message."""
    print_basic_args_help()
    output = mock_console.file.getvalue()
    print(output)
    assert "Opsbox opsbox.Arguments" in output


def test_print_missing_arguments_error(mock_console):
    """Test the missing arguments error message."""

    class MockFieldInfo:
        description = "desc"

    modules = ["module1"]
    arguments = [("arg1", "plugin1", MockFieldInfo())]

    print_missing_arguments_error(modules, arguments)
    output = mock_console.file.getvalue()
    assert "You are missing arguments for pipeline" in output
    assert "plugin1" in output
