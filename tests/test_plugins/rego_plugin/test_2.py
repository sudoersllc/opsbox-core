from pluggy import HookimplMarker
from pydantic import BaseModel, Field

from opsbox.plugins import Result

# Define a hookimpl (implementation of the contract)
hookimpl = HookimplMarker("opsbox")


class Test2:
    """Second test plugin."""

    @hookimpl
    def report_findings(self, data: "Result"):
        """Report the findings of the plugin.
        Attributes:
            data (CheckResult): The result of the checks.
        Returns:
            str: The formatted string containing the findings.
        """

        return [data]

    @hookimpl
    def grab_config(self):
        """Grab the configuration for the plugin."""

        class TestConfig(BaseModel):
            """Test configuration."""

            test2: str = Field(..., description="Test field.")

        return TestConfig
