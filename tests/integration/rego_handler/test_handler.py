from modules.handlers.rego_handler.rego_handler import RegoHandler

from opsbox.plugins import PluginFlow, Result
from unittest.mock import MagicMock
from tests.mocks import MockPlugin, MockConfig, MockRegistry
from tests.test_plugins.rego_plugin.test_2 import Test2

# ruff: noqa: S101


def config():
    """Fixture for the config."""
    return


def test_plugins():
    """Fixture for the plugins."""
    appconfig = MockConfig(path="test.json")
    # make mock plugins
    plugin = MockPlugin(
        Test2,
        "rego",
        appconfig=config(),
        extra={"rego": {"description": "Check for inactive S3 objects.", "rego_file": "test_2.rego"}},
        uses=[],
    )
    plugin.toml_path = "tests/test_plugins/rego_plugin/manifest.toml"

    handler = MockPlugin(RegoHandler, "handler", extra={"handles": ["rego"]}, appconfig=appconfig, uses=[])

    return plugin, handler, appconfig


def test_add_hookspecs():
    """Test the add_hookspecs method."""
    handler = RegoHandler()
    manager = MagicMock()
    handler.add_hookspecs(manager)
    assert manager.add_hookspecs.called
    assert manager.add_hookspecs.call_count == 1
    assert manager.add_hookspecs.call_args_list[0][0][0].__name__ == "RegoSpec"


def test_process_plugin():
    """Test the process_plugin method."""
    plugin, handler, conf = test_plugins()
    prior_results = [
        Result(
            relates_to="test",
            result_name="test",
            result_description="Test result.",
            details={"test": "test"},
            formatted="Test 1 result.",
        )
    ]
    result = handler.plugin_obj.process_plugin(
        plugin,
        prior_results,
        MockRegistry(
            plugins=[plugin, handler],
            flow=PluginFlow(input_plugins=["test_plugin_2"], output_plugins=["test_plugin_4"]),
            plugin_dir="tests/test_plugins",
        ),
    )
    assert result[0].result_name == "Test2"
    assert result[0].relates_to == "Test2"
    assert result[0].result_description == "Check for inactive S3 objects."
    assert result[0].details == []
