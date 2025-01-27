import pytest
from modules.handlers.general_handler.general_handler import GeneralHandler
from opsbox.plugins import PluginFlow, Registry

from unittest.mock import MagicMock

from opsbox.plugins import Result

# ruff: noqa: S101


@pytest.fixture(scope="module")
def test_registry():
    """Fixture for the registry with a dummy pipeline."""
    pipeline = PluginFlow(input_plugins=["test_plugin_1"], output_plugins=["test_plugin_4"])
    return Registry(flow=pipeline, plugin_dir="tests/test_plugins")


def test_add_hookspecs():
    """Test the add_hookspecs method."""
    handler = GeneralHandler()
    manager = MagicMock()
    handler.add_hookspecs(manager)
    assert manager.add_hookspecs.called
    assert manager.add_hookspecs.call_count == 4
    assert manager.add_hookspecs.call_args_list[0][0][0].__name__ == "AssistantSpec"
    assert manager.add_hookspecs.call_args_list[1][0][0].__name__ == "OutputSpec"
    assert manager.add_hookspecs.call_args_list[2][0][0].__name__ == "ProviderSpec"
    assert manager.add_hookspecs.call_args_list[3][0][0].__name__ == "InputSpec"


def test_process_input_plugin(test_registry: Registry):
    """Test the process_plugin method with an input."""
    handler = GeneralHandler()
    plugin = MagicMock()
    prior_results = []
    plugin = [item for item in test_registry.active_plugins if item.type == "input"][0]
    result: list["Result"] = handler.process_plugin(plugin, prior_results, test_registry)
    assert type(result) and result[0].result_name == "test1"


def test_process_output_plugin(test_registry: Registry):
    """Test the process plugin method with an output plugin."""
    handler = GeneralHandler()
    plugin = MagicMock()
    print(test_registry.active_plugins)
    plugin = [item for item in test_registry.active_plugins if item.type == "output"][0]

    item = Result(
        relates_to="test1",
        result_name="test1",
        result_description="Test result.",
        details={"test": "test"},
        formatted="Test 1 result.",
    )

    handler.process_plugin(plugin, [item], test_registry)
