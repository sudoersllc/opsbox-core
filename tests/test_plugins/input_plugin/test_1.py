from pluggy import HookimplMarker
from loguru import logger
from pydantic import BaseModel, Field

from core.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class Test1:
    """First test plugin."""

    @hookimpl
    def process(self, data: list["Result"]) -> list["Result"]:
        """Process the data."""
        item = Result(
            relates_to="test",
            result_name="test1",
            result_description="Test result.",
            details={"test": "test"},
            formatted="Test 1 result.",
        )
        logger.info("Processing data.")
        return [item]

    @hookimpl
    def grab_config(self):
        """Grab the configuration for the plugin."""

        class TestConfig(BaseModel):
            """Test configuration."""

            test1: str = Field(..., description="Test field.")

        return TestConfig
