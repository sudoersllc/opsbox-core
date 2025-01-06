from pluggy import HookimplMarker
from pydantic import BaseModel
from typing import TYPE_CHECKING
from loguru import logger

hookimpl = HookimplMarker("opsbox")


if TYPE_CHECKING:
    from core.plugins import Result


class CLIOutput:
    """CLI output plugin."""

    @hookimpl
    def grab_config(self):
        """"""

        class CLIConfig(BaseModel):
            """Configuration for the CLI output."""

            pass

        return CLIConfig

    @hookimpl
    def proccess_results(self, results: list["Result"]):
        """
        Prints the check results.

        Args:
            results (list[FormattedResult]): The formatted results from the checks.
        """
        logger.info("Check Results:")
        for result in results:
            logger.info(result.formatted)
