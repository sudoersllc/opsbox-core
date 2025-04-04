import importlib.metadata
import types
import pluggy
import importlib.util
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
import runpy

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

    def _available_in_dir(self, plugin_dir: str | Path) -> list[PluginInfo]:
        """Get the plugins from the specified directory.

        Args:
            plugin_dir (str): The directory to load the plugins from.

        Returns:
            list[PluginInfo]: List of plugins in the directory."""

        plugin_dir = Path(plugin_dir) if type(plugin_dir) is str else plugin_dir

        if not plugin_dir.exists():
            logger.warning(f"Plugin directory {plugin_dir} does not exist!")
            return []

        if not plugin_dir.is_dir():
            logger.warning(f"Plugin directory {plugin_dir} is not a directory!")
            return []

        excluded = ["pyproject.toml"]
        files_to_investigate = [item for item in plugin_dir.rglob("*.toml") if item.name not in excluded]

        logger.debug(f"Found {len(files_to_investigate)} files to investigate in {plugin_dir}", extra={"files": [str(item) for item in files_to_investigate]})

        skipped: list[str] = []  # store skipped plugins
        available: list[PluginInfo] = []

        for potential_manifest in files_to_investigate:
            try:
                info = self._parse_manifest(potential_manifest)
                plugin_class = self._grab_plugin_class(Path(info.toml_path).parent, info)
                info.plugin_obj = plugin_class()
                with contextlib.suppress(AttributeError):
                    config: type[BaseModel] = info.plugin_obj.grab_config()
                    info.config = config
                available.append(info)
            except Exception as e:
                skipped.append({str(potential_manifest): e})

        if len(skipped) > 0:
            logger.trace(f"Skipped {len(skipped)} invalid TOML manifests.", extra={"skipped_paths": skipped})
        logger.debug(f"Found {len(available)} available plugins in {plugin_dir}", extra={"available": [item.name for item in available]})
        return available

    def _available_in_entrypoints(self) -> list[PluginInfo]:
        """Get the plugins from the entrypoints.

        Returns:
            list[PluginInfo]: List of plugins in the entrypoints."""

        entry_points = importlib.metadata.entry_points(group=f"{self.project_name}.plugins")
        available: list[PluginInfo] = []

        logger.trace(f"Found {len(entry_points)} entry points in the environment", extra={"entry_points": [str(item) for item in entry_points]})

        for entry_point in entry_points:
            try:
                # grab entry point referenced obj and load it
                plugin_class = entry_point.load()
                module = importlib.import_module(plugin_class.__module__)
                file = Path(module.__file__)
                plugin_obj = plugin_class()

                # get manifest info and config
                manifest_path = file.parent / "manifest.toml"
                info = self._parse_manifest(manifest_path)
                info.plugin_obj = plugin_obj

                with contextlib.suppress(AttributeError):
                    config: type[BaseModel] = plugin_obj.grab_config()
                    info.config = config

                available.append(info)  # add to available plugins
            except Exception as e:
                logger.warning(f"Error loading plugin at entry point {entry_point.name}: {e}")

        logger.trace(f"Found {len(available)} available plugins in entry points", extra={"available": [item.name for item in available]})
        return available

    def _parse_manifest(self, manifest_path: Path) -> PluginInfo:
        """Parse the manifest file and return the plugin information.

        Args:
            path (Path): The path to the manifest file.

        Returns:
            PluginInfo: The plugin information.

        Raises:
            ValidationError: If the manifest file is invalid.
            FileNotFoundError: If the manifest file does not exist.
            KeyError: If the manifest file is missing required fields.
            toml.TOMLDecodeError: If the manifest file is not a valid TOML file.
        """
        if not isinstance(manifest_path, Path):
            manifest_path = Path(manifest_path)

        if not manifest_path.exists():
            logger.warning(f"Manifest file {manifest_path} does not exist!")
            return None

        if not manifest_path.is_file():
            logger.warning(f"Manifest file {manifest_path} is not a file!")
            return None

        with open(manifest_path, "rb") as toml_file:
            try:
                manifest = toml.load(toml_file)

                # fill in the empty info
                base_dict = {key: value for key, value in manifest["info"].items()}
                base_dict["toml_path"] = str(manifest_path)
                extra_dict = {key: value for key, value in manifest.items() if key != "info"}
                extra_dict = {"extra": extra_dict}

                concat_info = {**base_dict, **extra_dict}

                # validate with pydantic
                info = PluginInfo(**concat_info)
                return info
            except ValidationError as e:
                logger.trace(f"Error validating plugin {manifest_path}: {e.errors()}")
                raise e
            except KeyError as e:
                logger.trace(f"Invalid plugin info at {manifest_path}")
                raise e
            except toml.TOMLDecodeError as e:
                logger.trace(f"Error decoding TOML file {manifest_path}: {e}")
                raise e

    @property
    def available_plugins(self) -> list[PluginInfo]:
        """Get the available plugins in the plugin directory.
        This does not load the plugins.

        Returns:
            list[PluginInfo]: List of available plugins."""

        # check and return cache
        if len(self._available) > 0:
            logger.debug("Returning cached available plugins")
            return self._available

        logger.debug("No cached available plugins, computing available plugins from the environment")

        available: list[PluginInfo] = []

        # load bundled plugins
        if self.load_bundled:
            logger.debug("Loading bundled plugins")
            plugin_dir = __file__
            plugin_dir = Path(plugin_dir).parent / "bundled"
            available.extend(self._available_in_dir(plugin_dir))

        # load unbundled plugins
        if self.plugin_dir is not None:
            available.extend(self._available_in_dir(self.plugin_dir))
        else:
            available.extend(self._available_in_entrypoints())

        self._available = available
        return available

    @property
    def active_plugins(self) -> list[PluginInfo]:
        """Get the active plugins in the plugin directory along with their configurations.

        Returns:
            list[PluginInfo]: List of active plugins."""
        if len(self._active) > 0:
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
        requested_plugins: list[PluginInfo] = []
        for item in [item for item in self.available_plugins if item.name in pipeline_modules]:
            if item.name not in [item.name for item in requested_plugins]:
                requested_plugins.append(item)
            else:
                logger.warning(f"Duplicate plugin {item.name} found in pipeline, skipping")

        # check if we have all the needed plugins
        if len(pipeline_modules) > len(requested_plugins):
            names: list[str] = [item.name for item in requested_plugins]
            still_needed = [item for item in pipeline_modules if item not in names]
            logger.critical(f"Could not find the plugins you specified in the pipeline: {still_needed}")
            raise PluginNotFoundError(still_needed)
        elif len(pipeline_modules) != len(requested_plugins):
            logger.critical("Found all the plugins and then some! Something fishy is going on here, it's not safe to continue...")

        # load the plugins that are needed for the pipeline
        logger.trace(f"Collecting information for {len(requested_plugins)} plugins", extra={"collecting_plugins": [item.name for item in requested_plugins]})
        for item in requested_plugins:
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
            names = [item.name for item in dependecies]
            still_needed = [item for item in uses if item not in names]
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
        """Grab the plugin class from the specified path.
        This is used to load the plugin class from the specified path.

        Args:
            path (Path): The path to the plugin directory.
            plugin_info (PluginInfo): The plugin information.

        Returns:
            Any: The plugin class.

        Raises:
            FileNotFoundError: If the plugin file does not exist.
            AttributeError: If the class is not found in the module.
        """
        module_name, class_name = plugin_info.module, plugin_info.class_name
        filename = module_name.split(".")[-1] + ".py"  # Just get the filename
        plugin_file = path / filename

        logger.trace(f"Grabbing plugin class {class_name} from {plugin_file}")

        try:
            if not plugin_file.exists():
                raise FileNotFoundError(f"Plugin file not found: {plugin_file}")

            # load with runpy
            module_globals = runpy.run_path(str(plugin_file))

            # set up as module
            mod = types.ModuleType(module_name) if module_name not in sys.modules else sys.modules[module_name]
            mod.__dict__.update(module_globals)
            mod.__name__ = module_name
            mod.__package__ = module_name
            mod.__file__ = str(plugin_file)
            mod.__module__ = module_name

            sys.modules[module_name] = mod

            # import the module and get the class
            module = importlib.import_module(module_name)

            cls = getattr(module, class_name)

            cls.__module__ = module_name
            cls.__file__ = str(plugin_file)
            cls.__name__ = class_name

            if cls is None:
                raise AttributeError(f"Class '{class_name}' not found in module '{module_name}'")

            return cls
        except Exception as e:
            import traceback

            logger.debug(
                f"Failed to grab plugin class {class_name} from {module_name}: {e}",
                extra={"Exception": str(e), "Traceback": traceback.format_exc()},
            )
            raise e

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
