import pytest

from opsbox.plugins import PluginInfo, Registry, PluginFlow
from importlib import metadata
from pytest_mock import MockerFixture
from typing import Any
from loguru import logger


@pytest.fixture(scope="function")
def test_registry():
    """Fixture for the registry with a dummy pipeline."""
    Registry._instances = {}
    pipeline = PluginFlow(input_plugins=["test_plugin_1", "test_plugin_2"], output_plugins=["test_plugin_4"])
    yield Registry(flow=pipeline, plugin_dir="tests/test_plugins")
    Registry._instances = {}


# MOCKS FROM https://stackoverflow.com/questions/79386183/how-can-i-test-that-python-package-entrypoints-are-correctly-discovered-and-load
# ALL APPROPRIATE CREDIT GOES TO THE AUTHORS OF THE ABOVE LINKED POST


def make_entry_point_from_plugin(name: str, cls: type[Any], dist: metadata.Distribution | None = None) -> metadata.EntryPoint:
    """
    Create and return an importlib.metadata.EntryPoint object for the given
    plugin class.
    """
    group: str | None = getattr(cls, "group", "opsbox.plugins")
    ep = metadata.EntryPoint(
        name=name,
        group=group,  # type: ignore[arg-type]
        value=f"{cls.__module__}:{cls.__class__.__name__}",
    )

    if dist:
        ep = ep._for(dist)  # type: ignore[attr-defined,no-untyped-call]
        return ep

    return ep


def make_entry_points(mocker: MockerFixture, to_convert: list[tuple[Any, str]]) -> None:
    """Create entrypoints from tuples.

    Args:
        mocker (MockerFixture): The mocker to use when mocking the values.
        to_convert (list[tuple[Any, str]]): List of tuples to convert to entrypoints.
    """
    entry_points = []
    for plugin, name in to_convert:
        entry_points.append(make_entry_point_from_plugin(name, plugin))

    mocker.patch.object(
        metadata,
        "entry_points",
        return_value=entry_points,
    )
    return


@pytest.fixture(scope="function")
def registry_no_plugindir(mocker: MockerFixture, test_registry: Registry):
    """Convert all available plugins to entrypoints."""
    # grab available plugins from the initial registry
    logger.info("Grabbing available from initial registry")

    available_info: list[PluginInfo] = []
    for available_plugin in test_registry.available_plugins:
        logger.debug(f"Converting {available_plugin.name} to entrypoint")
        available_info.append(available_plugin)

    # erase the registry
    logger.info("Nuking the registry")
    Registry._instances = {}

    # mock the entrypoints
    logger.info("Mocking the entrypoints")
    make_entry_points(mocker, [(plugin.plugin_obj, plugin.name) for plugin in available_info])

    # create a new registry
    logger.info("Creating a new registry")
    pipeline = PluginFlow(input_plugins=["test_plugin_1", "test_plugin_2"], output_plugins=["test_plugin_4"])
    return Registry(flow=pipeline)
