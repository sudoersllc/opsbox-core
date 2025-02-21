import importlib.metadata
import pluggy
import importlib.util
import os
import sys
import tomllib as toml
from pydantic import BaseModel
from opsbox.base_hooks import add_hookspecs
from opsbox.utils import SingletonMeta
from typing import Any
from loguru import logger
from pathlib import Path
import contextlib
from pydantic import ValidationError
from typing import Type
import importlib_resources as resources
from inspect import getmodule

hookspec = pluggy.HookspecMarker("opsbox")


class PluginNotFoundError(Exception):
    """Exception raised when a plugin is not found.

    Attributes:
        plugin_name (str | list[str]): The name of the plugin that was not found.
        message (str): The message of the exception.
    """

    def __init__(self, plugin_name: str | list[str]):
        self.plugin_name = plugin_name
        if isinstance(plugin_name, list):
            self.message = f"Plugins {', '.join(plugin_name)} not found."
        else:
            self.message = f"Plugin '{plugin_name}' not found."
        super().__init__(self.message)


class Result(BaseModel):
    """A dictionary representing the results of a rego check.

    Attributes:
        relates_to (str): The thing that the result relates to.
        result_name (str): The name of the result.
        result_description (str): The description of the result.
        details (dict | list[dict]): The details of the result.
        formatted (str): The formatted string of the result.
    """

    relates_to: str
    result_name: str
    result_description: str
    details: dict | list[dict]
    formatted: str


class PluginInfo(BaseModel):
    """Model for the plugin information.

    Attributes:
        name (str): The name of the plugin.
        module (str): The module of the plugin.
        class_name (str): The class of the plugin.
        type (str): The type of the plugin.
        toml_path (str): The path to the TOML file.
        plugin_obj (Any | None): The plugin object.
        config (BaseModel | None): The configuration of the plugin.
        uses (list[str] | None): The plugins that the plugin uses.
        extra (dict[str, Any] | None): Extra information about the plugin.
    """

    name: str
    module: str
    class_name: str
    type: str
    toml_path: str | Path
    plugin_obj: Any | None = None
    config: Type[BaseModel] | None = None
    uses: list[str] = []
    extra: dict[str, Any] | None = None


class PluginFlow(BaseModel):
    """Basic flow model for the plugins.

    Attributes:
        input_plugins (list[str]): List of input plugins.
        assistant_plugins (list[str]): List of assistant plugins.
        output_plugins (list[str]): List of output plugins.
    """

    input_plugins: list[str] = []
    assistant_plugins: list[str] = []
    output_plugins: list[str] = []

    def set_flow(self, pipeline: str) -> "PluginFlow":
        """Processes the pipeline for the application.
        This method is used to process the pipeline from strings.

        Args:
            pipeline (str): The pipeline to process.
        """

        raw_pipeline = pipeline.split("-")
        input_modules = raw_pipeline.pop(0).split(",")
        output = raw_pipeline.pop().split(",")
        in_between = raw_pipeline

        self.input_plugins = input_modules
        self.assistant_plugins = in_between
        self.output_plugins = output

        return self

    @property
    def all_visible_modules(self) -> list[str]:
        """Returns all visible modules in the pipeline.

        Returns:
            list[str]: All modules in the pipeline.
        """
        return self.input_plugins + self.assistant_plugins + self.output_plugins


class Registry(metaclass=SingletonMeta):
    """Registry for the plugins. This is a singleton class.

    Attributes:
        project_name (str): The project name for the plugin manager.
        plugin_dir (str): Directory where the plugins are located.
        manager (pluggy.PluginManager): The plugin manager instance.
        flow (PluginFlow): The flow of the plugins.
        handlers (dict[str, Any]): The handlers for the plugins.
        activated (set[str]): The activated plugins.
        handlers (dict[str, Any]): The handlers for the plugins."""

    project_name = "opsbox"
    handlers = {}
    _active = []
    _available = []

    def __init__(self, flow: PluginFlow, plugin_dir: str | None = None, load_bundled: bool = True):
        self.flow = flow
        self.load_bundled = load_bundled
        self.manager = pluggy.PluginManager(self.project_name)
        if plugin_dir is not None:
            logger.debug(f"Using plugins from directory {plugin_dir}")
            self.plugin_dir = plugin_dir
        else:
            logger.debug("Using plugins from entrypoints in .venv")
            self.plugin_dir = None
            plugin_num = self.manager.load_setuptools_entrypoints(f"{self.project_name}.plugins")
            logger.debug(f"Found {plugin_num} plugins")
        add_hookspecs(self.manager)

    def add_handler(self, plugin: PluginInfo) -> None:
        """Add a handler to the manager.
        Handlers are plugins that handle other plugins of specified types.

        Args:
            plugin (PluginInfo): The plugin to add as a handler."""
        logger.trace(f"Adding handler {plugin.name}")
        handles_type = plugin.extra["handler"]["handles"]
        for x in handles_type:
            if x not in self.handlers:
                self.handlers[x] = plugin.plugin_obj
                with contextlib.suppress(ValueError, AttributeError):
                    plugin.plugin_obj.add_hookspecs(self.manager)

    def read_toml_spec(self, path: Path, log: bool = True) -> PluginInfo:
        """Read the TOML file and validate the plugin spec.

        Args:
            path (Path): The path to the TOML file.
            log (bool): Whether to log errors or not.

        Returns:
            PluginInfo: The plugin information.
        """
        with open(path, "rb") as toml_file:
            try:
                plugin_config = toml.load(toml_file)

                # seperate basic plugin info from other info
                plugin_info = plugin_config["info"]
                plugin_info["toml_path"] = str(path)
                plugin_extra = {k: v for k, v in plugin_config.items() if k != "info"}
                plugin_extra = {"extra": plugin_extra}

                concat_info = {**plugin_info, **plugin_extra}

                # validate with pydantic
                if log:
                    logger.debug(f"Validated plugin {path}")
                return PluginInfo(**concat_info)
            except ValidationError as e:
                if log:
                    logger.warning(f"Error validating plugin {path}: {e.errors()}")
                raise e
            except KeyError:
                if log:
                    logger.warning(f"Invalid plugin info at {path}")
                raise KeyError
            except toml.TOMLDecodeError as e:
                if log:
                    logger.warning(f"Error decoding TOML file {path}: {e}")
                raise e

    @property
    def available_plugins(self) -> list[PluginInfo]:
        """Get the available plugins in the plugin directory.
        This does not load the plugins.

        Returns:
            list[PluginInfo]: List of available plugins."""
        available: list[PluginInfo] = []
        if len(self._available) > 0:
            logger.debug("Returning cached available plugins")
            return self._available
        else:
            logger.debug("No cached available plugins, computing available plugins from the environment")

            def _grab_plugins_from_dir(plugin_dir: Path) -> list[PluginInfo]:
                logger.debug(f"Finding plugins available in directory {plugin_dir}")
                skipped: list[str] = []  # store skipped plugins
                for item in Path(plugin_dir).rglob("*.toml"):
                    try:
                        info = self.read_toml_spec(item, log=False)
                        plugin_class = self._grab_plugin_class(Path(info.toml_path).parent, info)
                        info.plugin_obj = plugin_class()
                        with contextlib.suppress(AttributeError):
                            config: type[BaseModel] = info.plugin_obj.grab_config()
                            info.config = config
                    except Exception:
                        skipped.append(str(item))
                        continue
                    if info is not None:
                        available.append(info)
                if len(skipped) > 0:
                    logger.trace(f"Skipped {len(skipped)} invalid TOML manifests.", extra={"skipped_paths": skipped})

            if self.load_bundled:
                file_dir = Path(__file__).parent.joinpath("bundled")
                _grab_plugins_from_dir(file_dir)

            # load unbundled plugins
            if self.plugin_dir is not None:
                # load the plugins from the plugin directory if specified
                _grab_plugins_from_dir(Path(self.plugin_dir))
            else:
                # load the plugins from the entrypoints if not specified
                logger.debug("No plugin directory specified. Finding plugins availble from entrypoints in venv.")
                for entry_point in importlib.metadata.entry_points(group=f"{self.project_name}.plugins"):
                    try:
                        plugin_class = entry_point.load()
                        plugin_obj = plugin_class()
                        config = None
                        with contextlib.suppress(AttributeError):
                            config: type[BaseModel] = plugin_obj.grab_config()

                        plugin_module = getmodule(plugin_class)
                        with resources.files(plugin_module).joinpath("manifest.toml") as path, open(path, "rb") as toml_file:
                            plugin_config = toml.load(toml_file)
                            plugin_raw_info = plugin_config["info"]
                            plugin_raw_info["toml_path"] = path
                            plugin_raw_info["extra"] = {k: v for k, v in plugin_config.items() if k != "info"}
                            plugin_raw_info["config"] = config
                            plugin_raw_info["plugin_obj"] = plugin_obj
                            plugin_raw_info["class_name"] = plugin_class.__name__
                            plugin_raw_info["module"] = plugin_class.__module__

                            info = PluginInfo(**plugin_raw_info)
                        available.append(info)
                    except Exception as e:
                        logger.warning(f"Error loading plugin at entry point {entry_point.name}: {e}")
                        continue
            available_names = [item.name for item in available]
            self._available = available
            logger.debug(f"Found {len(available)} available plugins in {(self.plugin_dir if self.plugin_dir is not None else 'entrypoints')}", extra={"available": available_names})
            return available

    @property
    def active_plugins(self) -> list[PluginInfo]:
        """Get the active plugins in the plugin directory along with their configurations.

        Returns:
            list[PluginInfo]: List of active plugins."""
        if len(self._active) != 0:
            logger.debug("Returning cached active plugins")
            return self._active

        logger.debug("No cached active plugins found, computing active plugins")

        active: list[PluginInfo] = []
        dependecies: set[PluginInfo] = set()
        uses: list[str] = []

        pipeline_modules = set(self.flow.all_visible_modules)

        rebuilt_pipeline_str = ", ".join(self.flow.input_plugins) + ("-" + "-".join(self.flow.assistant_plugins) if self.flow.assistant_plugins else "") + "-" + "-".join(self.flow.output_plugins)
        logger.trace(f"Starting first-pass plugin resolution for pipeline: {rebuilt_pipeline_str}")

        # get the plugins that are specifically requested for the pipeline
        shallow_needed: list[PluginInfo] = []
        for item in [item for item in self.available_plugins if item.name in pipeline_modules]:
            if item not in shallow_needed:
                shallow_needed.append(item)

        # check if we have all the needed plugins
        if len(pipeline_modules) != len(shallow_needed):
            names: list[str] = [item.name for item in shallow_needed]
            still_needed = [item for item in pipeline_modules if item not in names]
            logger.critical(f"Could not find the plugins you specified in the pipeline: {still_needed}")
            raise PluginNotFoundError(still_needed)

        # load the plugins that are needed for the pipeline
        logger.trace(f"Collecting information for {len(shallow_needed)} plugins", extra={"collecting_plugins": [item.name for item in shallow_needed]})
        for item in shallow_needed:
            if item.type == "handler":
                self.add_handler(item)
            active.append(item)
            uses.extend(item.uses)

        logger.trace(f"First-pass plugin resolution complete for pipeline: {rebuilt_pipeline_str}", extra={"pipeline_plugins": [item.name for item in active], "dependencies_needed": uses})

        logger.trace(f"Starting second-pass plugin resolution for pipeline: {rebuilt_pipeline_str}")
        uses = set(uses)
        dependecies = []
        for item in [item for item in self.available_plugins if item.name in uses]:
            if item not in dependecies:
                dependecies.append(item)

        # check if we have all the dependencies
        if len(uses) != len(dependecies):
            still_needed = [item for item in uses if item not in dependecies]
            logger.critical(f"Could not find needed plugin dependencies: {still_needed}")
            raise PluginNotFoundError(still_needed)

        # load the plugins that are needed for the other plugins
        logger.trace(f"Collecting information for {len(dependecies)} dependencies", extra={"collecting_dependencies": [item.name for item in dependecies]})
        for item in dependecies:
            if item.type == "handler":
                self.add_handler(item)
            active.append(item)

        logger.trace(f"Second-pass plugin resolution complete for pipeline: {rebuilt_pipeline_str}", extra={"active_plugins": [item.name for item in active]})
        logger.trace("Caching active plugins")
        logger.debug(f"Computed {len(active)} active plugins")
        self._active = active
        return active

    @active_plugins.setter
    def active_plugins(self, value):
        self._active = value

    # @logger.catch(reraise=True)
    def _grab_plugin_class(self, path: Path, plugin_info: PluginInfo) -> Any:
        """Load the class from the plugin module.

        Args:
            path (Path): Path to the plugin file.
            plugin_info (PluginInfo): Configuration of the plugin.

        Returns:
            Any: Loaded class from the plugin module.
        """
        module_name, class_name = plugin_info.module, plugin_info.class_name
        logger.trace(f"Grabbing plugin class {class_name} from {module_name} at {path}")
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(str(path), f"{module_name}.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    # @logger.catch(reraise=True)
    def load_active_plugins(self, config: dict) -> list[tuple[str, str, Any]] | None:
        """Load the active plugins with the provided configuration.

        Args:
            config (dict): The configuration to load the plugins with.

        Returns:
            list[tuple[str, str, Any]] | None: A list of needed fields if any are missing."""
        logger.debug("Loading all active plugins")
        still_needed = []

        # load the active plugins
        for plugin in self.active_plugins:
            try:
                self.load_plugin(config, plugin)  # load the plugin
            except ValidationError:  # missing fields
                plugin_config_model = plugin.config
                if plugin_config_model is None:
                    # no needed fields
                    continue
                else:  # collect needed fields
                    needed = [(name, plugin.name, info) for name, info in plugin_config_model.model_fields.items() if (name not in config) and (info.is_required)]
                    still_needed.extend(needed)
                continue

        # return needed fields if any
        if len(still_needed) > 0:
            return still_needed
        else:
            return None

    def load_plugin(self, config: dict, plugin: PluginInfo):
        """Load a specified with the provided configuration.

        Args:
            config (dict): The configuration to load the plugin with.
            plugin (PluginInfo): The plugin to load.
        """
        logger.debug(f"Spinning up plugin {plugin.name}")
        plugin_obj = plugin.plugin_obj
        try:
            self.manager.register(plugin_obj, name=plugin.name)
        except ValueError as e:
            logger.warning(f"Plugin {plugin.name} already registered: {e}")
            pass
        with contextlib.suppress(AttributeError):
            if plugin.config is not None:
                item_config = plugin.config(**config)
                plugin_obj.set_data(item_config)
            plugin_obj.activate()

    def process_pipeline(self):
        """Process the pipeline.
        Runs all the plugins in their specified order.

        Args:
            pipeline (Pipeline): The pipeline to process."""

        # get the plugins in the pipeline
        plugin_set = self.active_plugins
        input_plugins = [plugin for plugin in plugin_set if plugin.name in self.flow.input_plugins]
        assistant_plugins = [plugin for plugin in plugin_set if plugin.name in self.flow.assistant_plugins]
        output_plugins = [plugin for plugin in plugin_set if plugin.name in self.flow.output_plugins]

        results = []  # store the results of the pipeline
        # process the input plugins
        logger.info(f"Processing {len(input_plugins)} input plugins")
        for plugin in input_plugins:
            result = self.handlers[plugin.type].process_plugin(plugin, [], self)  # dispatch the plugin to handler
            results.append(result)

        # process the assistant plugins, if any
        if len(assistant_plugins) == 0:
            logger.info("No assistant plugins found, skipping")
            assistant_results = results  # skip assistant plugins
        else:
            logger.info(f"Processing {len(assistant_plugins)} assistant plugins")
            assistant_results = []
            for plugin in assistant_plugins:
                mixed_results = assistant_results.copy()
                for x in results:
                    if x is type(list):
                        for y in x:
                            mixed_results.append(y)
                    else:
                        mixed_results.append(x)

                # dispatch the plugin to handler
                # uses progressivly more results as the pipeline progresses
                result = self.handlers[plugin.type].process_plugin(plugin, mixed_results, self)
                if isinstance(result, list):
                    for x in result:
                        assistant_results.append(x)
                else:
                    assistant_results.append(result)

        # process the output plugins
        logger.info(f"Processing {len(output_plugins)} output plugins")
        for plugin in output_plugins:
            self.handlers[plugin.type].process_plugin(plugin, assistant_results, self)  # dispatch the plugin to handler
