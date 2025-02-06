from opsbox.plugins import Registry
from pathlib import Path

# ruff: noqa: S101

def test_grab_class(test_registry: Registry):
    """Test the grab class method."""
    # Grab the registry and plugins
    registry = test_registry
    rego_plugin = [item for item in registry.active_plugins if item.name == "test_plugin_2"][0]

    # Grab the rego plugin
    plugin_path = Path("tests/test_plugins/rego_plugin/")
    plugin = registry._grab_plugin_class(plugin_path, rego_plugin)

    # Assert proprt class name
    assert plugin.__name__ == "Test2"

def test_loading_active_fail(test_registry: Registry):
    """Test the loading of active plugins."""
    registry = test_registry
    needed = registry.load_active_plugins({})

    # test if proper missing fields are raised
    assert len(needed) == 3

def test_loading_active_success(test_registry: Registry):
    """Test the loading of active plugins."""
    registry = test_registry
    registry.active_plugins = [item for item in registry.active_plugins if item.name != "test_plugin_3"]

    test_conf = {
        "test1": "test",
        "test2": "test",
        "test3": "test",
    }

    needed = registry.load_active_plugins(test_conf)

    # test if proper missing fields are raised
    assert needed is None

def test_loading_active_success_from_entrypoints(registry_no_plugindir: Registry):
    """Test the loading of active plugins."""
    registry = registry_no_plugindir
    registry.active_plugins = [item for item in registry.active_plugins if item.name != "test_plugin_3"]

    test_conf = {
        "test1": "test",
        "test2": "test",
        "test3": "test",
    }

    needed = registry.load_active_plugins(test_conf)

    # test if proper missing fields are raised
    assert needed is None

def test_loading_active_fail_from_entrypoints(registry_no_plugindir: Registry):
    """Test the loading of active plugins."""
    registry = registry_no_plugindir
    needed = registry.load_active_plugins({})

    # test if proper missing fields are raised
    assert len(needed) == 3

def test_proccess_active_plugins(test_registry: Registry):
    """Test the processing of active plugins."""
    registry = test_registry
    registry.active_plugins = [item for item in registry.active_plugins if item.name != "test_plugin_3"]

    test_conf = {
        "test1": "test",
        "test2": "test",
        "test3": "test",
    }

    _ = registry.load_active_plugins(test_conf)
    registry.process_pipeline()