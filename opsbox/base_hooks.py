import pluggy
from pydantic import BaseModel
from loguru import logger

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opsbox.plugins import PluginInfo, Result, Registry


hookspec = pluggy.HookspecMarker("opsbox")


# Define a hookspec (contract for plugins)
class BaseSpec:
    """Base contract for all plugins.

    Allows for a series of basic operations that all plugins can have."""

    @hookspec
    def grab_config(self) -> type[BaseModel]:
        """Return the plugin's configuration pydantic model.
        These should be things your plugin needs/wants to function."""

    @hookspec
    def activate(self) -> None:
        """Initialize the plugin.
        Essentially a replacement for __init__."""

    @hookspec
    def set_data(self, model: BaseModel) -> None:
        """Set the data for the plugin based on the model.
        Normally, you can shove this in whatever class variable you want.

        Args:
            model (BaseModel): The data model for the plugin."""


class HandlerSpec:
    """Base contract for plugin handlers.

    Plugin handlers are plugins that handle other plugins of specified types."""

    @hookspec
    def add_hookspecs(self, manager: pluggy.PluginManager) -> None:
        """Add the hookspecs to the manager."""

    @hookspec
    def process_plugin(self, plugin: "PluginInfo", prior_results: list["Result"], registry: "Registry") -> list["Result"]:
        """Process the plugin."""


def add_hookspecs(manager: pluggy.PluginManager):
    """Adds basic hookspecs to the registry."""
    logger.trace("Adding hookspecs to the registry")
    manager.add_hookspecs(BaseSpec)
    manager.add_hookspecs(HandlerSpec)
