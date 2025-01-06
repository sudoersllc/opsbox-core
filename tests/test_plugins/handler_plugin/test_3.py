from pluggy import HookimplMarker
from loguru import logger
from pydantic import BaseModel, Field

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.plugins import Result, PluginInfo, Registry

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class Test3:
    """Third test plugin."""

    @hookimpl
    def process_plugin(
        self, plugin: "PluginInfo", prior_results: list["Result"], registry: "Registry"
    ) -> list["Result"]:
        """Process the plugin."""
        logger.info("Processing plugin.")

        return

    @hookimpl
    def grab_config(self):
        """Grab the configuration for the plugin."""

        class TestConfig(BaseModel):
            """Test configuration."""

            test3: str = Field(..., description="Test field.")

        return TestConfig
