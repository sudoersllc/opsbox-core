from pluggy import HookimplMarker
from core.plugins import Result


hookimpl = HookimplMarker("opsbox")


class Test5:
    """Fifth test plugin. Provider type."""

    def gather_data(self):
        """Gather data test."""

        item = Result(
            relates_to="test_plugin",
            result_name="test_plugin_5",
            result_description="Test plugin 5",
            details={"test": "test"},
            formatted="",
        )

        return item
