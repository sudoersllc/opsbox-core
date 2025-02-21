import importlib
import pytest

from opsbox.plugins import Registry, PluginFlow, PluginNotFoundError
from pathlib import Path

# ruff: noqa: S101


@pytest.fixture(scope="module")
def test_registry_bad():
    """Fixture for the registry with a dummy pipeline."""
    Registry._instances = {}
    pipeline = PluginFlow(input_plugins=["test_plugin_123", "test_plugin_234"], output_plugins=["test_plugin_456"])
    return Registry(flow=pipeline, plugin_dir="tests/test_plugins", load_bundled=False)


def test_available_plugins(test_registry: Registry):
    """Test the available plugins."""
    registry = test_registry
    plugins = registry.available_plugins

    assert len(plugins) == 5


def test_active_plugins_success(test_registry: Registry):
    """Test the active plugins."""
    registry = test_registry
    plugins = registry.active_plugins

    wanted_names = ["test_plugin_1", "test_plugin_2", "test_plugin_3", "test_plugin_4"]
    names = [plugin.name for plugin in plugins]
    assert all([name in wanted_names for name in names])

    plugin_dir_names = ["rego_plugin", "provider_plugin", "handler_plugin", "output_plugin", "input_plugin"]

    wanted_toml_paths = [Path(f"tests/test_plugins/{i}/manifest.toml") for i in plugin_dir_names]
    toml_paths = [Path(plugin.toml_path) for plugin in plugins]
    print(toml_paths)

    assert all([path in wanted_toml_paths for path in toml_paths])

    for plugin in plugins:
        if plugin.name == "test_plugin_1":
            assert plugin.type == "input"
            assert plugin.class_name == "Test1"
            assert plugin.config is not None
            assert plugin.plugin_obj is not None
        elif plugin.name == "test_plugin_2":
            assert plugin.type == "rego_test"
            assert plugin.class_name == "Test2"
            assert plugin.extra["rego"]["description"] == "Check for inactive S3 objects."
        elif plugin.name == "test_plugin_3":
            assert plugin.type == "handler"
            assert plugin.class_name == "Test3"
        elif plugin.name == "test_plugin_4":
            assert plugin.type == "output"


def test_active_plugins_no_deps(test_registry_bad: Registry):
    """Test the active plugins."""
    registry = test_registry_bad
    with pytest.raises(PluginNotFoundError):
        registry.active_plugins


def test_available_from_entrypoints(registry_no_plugindir: Registry):
    """Test the available plugins."""
    registry = registry_no_plugindir
    print(importlib.metadata.entry_points())
    plugins = registry.available_plugins

    assert len(plugins) == 5


def test_active_from_entrypoints(registry_no_plugindir: Registry):
    """Test the active plugins."""
    registry = registry_no_plugindir
    plugins = registry.active_plugins

    wanted_names = ["test_plugin_1", "test_plugin_2", "test_plugin_3", "test_plugin_4"]
    names = [plugin.name for plugin in plugins]
    assert all([name in wanted_names for name in names])

    for plugin in plugins:
        if plugin.name == "test_plugin_1":
            assert plugin.type == "input"
            assert plugin.class_name == "Test1"
            assert plugin.config is not None
            assert plugin.plugin_obj is not None
        elif plugin.name == "test_plugin_2":
            assert plugin.type == "rego_test"
            assert plugin.class_name == "Test2"
            assert plugin.extra["rego"]["description"] == "Check for inactive S3 objects."
        elif plugin.name == "test_plugin_3":
            assert plugin.type == "handler"
            assert plugin.class_name == "Test3"
        elif plugin.name == "test_plugin_4":
            assert plugin.type == "output"
