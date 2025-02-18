from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
import sys
from .plugins import Registry, PluginFlow
from opsbox.utils import SingletonMeta
from os import environ, path
import json
import dateparser


from loguru import logger


def find_config_file(filename: str) -> str | None:
    """Finds the configuration file in the user's home directory.

    Args:
        filename (str): The name of the configuration file.

    Returns:
        str | None: The path to the configuration file or None if the file is not found.
    """
    home_dir = path.expanduser("~")
    config_path = path.join(home_dir, filename)
    return config_path if path.isfile(config_path) else None


class ApplicationSettings(BaseModel):
    """The class is used to store the essential settings for the application.

    Attributes:
        modules (list[str]): The modules to load in pipeline format.
        config (str): The path to the configuration file.
        plugin_dir (str): The directory to load plugins from instead of environment. Useful for local development.
        log_level (str): The desired logging level. One of 'INFO', 'TRACE', 'DEBUG', 'WARNING', or 'CRITICAL'. Default is 'INFO'.
        log_file (str): The path to the desired logging file.
        init_debug (bool): Enable debug logging during initialization. Used as a flag.
        see_all (bool): Show all plugins, including handlers and providers. Used as a flag.
        help (bool): Show help for the program or specified pipeline pipeline. Used as a flag.
    """

    modules: list[str] | str = Field(..., description="List of modules to load in pipeline format.")
    config: str | None = Field(default=find_config_file(".opsbox_conf.json"), description="Path to the configuration file.")
    plugin_dir: str | None = Field(None, description="Directory to load plugins from instead of environment. Useful for local development.")
    log_level: str | None = Field(None, description="Desired logging level. One of 'INFO', 'TRACE', 'DEBUG', 'WARNING', or 'CRITICAL'. Default is 'INFO'")
    log_file: str | None = Field(None, description="Path to the desired logging file.")
    init_debug: bool = Field(False, description="Enable debug logging during initialization. Used as a flag.")
    see_all: bool = Field(False, description="Show all plugins, including handlers and providers. Used as a flag.")
    help: bool = Field(False, description="Show help for the program or specified pipeline pipeline. Used as a flag.")
    verbose: bool = Field(False, description="Enable verbose logging. Used as a flag.")


class LLMValidator(BaseModel):
    """
    LLM Validator.

    Validates the LLM configuration.

    """

    oai_key: str | None = Field(None, description="The OpenAI API key.")
    claude_key: str | None = Field(None, description="The secret key for Claude")


class AppConfig(metaclass=SingletonMeta):
    """The class is used to store the configuration for the application. The
    configuration can be loaded from a configuration file, environment variables,
    or command line arguments.

    This class is a singleton, meaning that only one instance of the class is
    created and that all subsequent instances return the same instance.

    Attributes:
        self.basic_settings (EssentialSettings): The basic settings for the application.
        self.module_settings (dict): The settings for the modules.
        self.plugin_flow (PluginFlow): The plugin flow for the application.
        self.registry (Registry): The registry for the application.
        self.llm (LLM | None): The LLM for the application.
        self.embed_model (LLMEmbedding | None): The LLM embedding model for the application.
    """

    def _parse_json_arguments(self, config_file: str, default_file_path: str = ".opsbox.json") -> dict | None:
        """Loads the configuration from the default configuration file, if it exists.
        Then, it loads the configuration from the specified configuration file.

        Args:
            config_file (str): The path to the configuration file.
            default_file_path (str): The path to the default configuration file from the user's home directory.

        Returns:
            dict | None: The configuration arguments. If no configuration is found, returns None.
        """
        # if default config file is set, load args from it
        logger.trace(f"Loading configuration from {config_file} and {default_file_path}...")
        conf = {}
        default_config_file = find_config_file(default_file_path)
        expected_path = path.expanduser(f"~/{default_file_path}")

        # load the default config file if it exists
        if default_config_file is not None:
            try:
                with open(default_config_file, "r") as f:
                    document = json.load(f)
                    conf.update(document)
                logger.trace(f"Loaded default config file {default_config_file}")
            except json.JSONDecodeError:
                logger.warning(f"Default config file at {expected_path} is not valid JSON.")
        else:
            logger.trace(f"No default config file found at {expected_path}.")

        # load the specified config file
        if config_file is not None:
            try:
                with open(config_file, "r") as f:
                    document = json.load(f)
                    conf.update(document)
                logger.trace(f"Loaded specified config file {config_file}")
            except FileNotFoundError:
                logger.error(f"Specified config file {config_file} not found.")
                raise FileNotFoundError(f"Config file {config_file} not found.")
            except json.JSONDecodeError as e:
                logger.error(f"Specified config file {config_file} is not valid JSON.")
                raise e

        return conf if conf != {} else None

    def _parse_cmd_arguments(self) -> dict | None:
        """Parse the command line arguments and return them as a dictionary.
        Can handle both --arg=value and --arg value formats.

        Returns:
            dict | None: The command line arguments in {arg: value} format. If no arguments are found, returns None.
        """
        logger.trace(f"Parsing {len(sys.argv) - 1} command line pieces...")

        raw_cmd_args = sys.argv[1:]  # Skip the script name and break the arguments into chunks

        # split the arguments into chunks of arguments, where the first element is the argument name
        # and the rest are the values associated with that argument
        processed_args = []
        current_slice = None
        for arg in raw_cmd_args:
            if arg.startswith("--"):  # we have a new argument
                # pop the current slice if it exists
                if current_slice is not None:
                    processed_args.append(current_slice)
                    current_slice = None

                # split the argument by "=" if it exists
                if "=" in arg:
                    single_arg = arg.split("=")
                    current_slice = [single_arg[0], single_arg[1]]
                else:
                    # otherwise, just add the argument
                    current_slice = [arg]
            else:
                current_slice.append(arg)

        # add the last slice if it exists
        if current_slice is not None:
            processed_args.append(current_slice)

        # define a helper function for converting numbers
        def convert_to_numeric(value: str) -> int | float | str | datetime:
            """Convert the value to an integer or float if possible.

            Args:
                value: The value to convert.

            Returns:
                int | float | str | datetime: The converted value.
            """
            # try to convert the value to an integer or float
            try:
                return int(value)
            except ValueError:
                pass

            try:
                return float(value)
            except ValueError:
                pass

            # try to convert the value to a datetime object
            item = dateparser.parse(value)
            if item is None:
                return value
            else:
                return item

        # process the arguments into a dictionary
        arg_dict = {}
        for arg_chunk in processed_args:
            arg_label = arg_chunk[0].replace("--", "")
            if len(arg_chunk) == 1:
                # if the argument doesn't have a value, set it to True
                # this is for flags like --help
                arg_dict[arg_label] = True
            elif len(arg_chunk) > 2:
                # if there are multiple arguments, replace the list with covnerted values
                arg_dict[arg_label] = [convert_to_numeric(arg) for arg in arg_chunk[1:]]
            else:
                # otherwise, just convert the value
                arg_dict[arg_label] = convert_to_numeric(arg_chunk[1])

        logger.trace(f"Processed {len(arg_dict)} command line arguments.")

        return arg_dict if arg_dict != {} else None

    def _grab_args(self) -> tuple[dict, PluginFlow]:
        """Grab the configuration arguments from the environment, command line, or configuration file.

        Returns:
            tuple[dict, PluginFlow]: The configuration arguments and the plugin flow."""
        total_config = {}

        # load the command line arguments
        cli_config = self._parse_cmd_arguments()
        if cli_config is not None:
            total_config.update(cli_config)
            logger.debug(f"Loaded {len(cli_config)} command line arguments.")

        # load the configuration from both the default and specified configuration files
        json_file_config = self._parse_json_arguments(config_file=total_config.get("config"))
        if json_file_config is not None:
            total_config.update(json_file_config)
            logger.debug(f"Loaded {len(json_file_config)} configuration file arguments.")

        # load environment variables
        lower_case_environ = {key.lower(): value for key, value in environ.items()}
        total_config.update(lower_case_environ)  # load any environment variables
        logger.debug(f"Loaded {len(lower_case_environ)} environment variables as configuration arguments.")

        # set the pipeline
        pipeline = PluginFlow().set_flow(total_config["modules"]) if "modules" in total_config else None

        return total_config, pipeline

    def init_llms(self) -> None:
        """Initialize the LLMs for the application."""
        # set the LLM
        if self.llm_settings.oai_key is not None:
            from llama_index.llms.openai import OpenAI
            from llama_index.embeddings.openai import OpenAIEmbedding

            self.llm = OpenAI(model="gpt-4o", api_key=self.llm_settings.oai_key, temperature=0.2)
            self.embed_model = OpenAIEmbedding(api_key=self.llm_settings.oai_key)
        elif self.llm_settings.claude_key is not None:
            from llama_index.llms.anthropic import Anthropic

            self.llm = Anthropic(model="claude-3-5-sonnet-20240620", api_key=self.llm_settings.claude_key)
            self.embed_model = None

    def load(self, all_fields: bool = False) -> None | list[tuple[str, str, FieldInfo]]:
        """Bootstraps the configuration code and sets the registry.

        This method is used to load the configuration data from the command line, environment variables,
        or a configuration file.

        Args:
            all_fields (bool): Whether to load all fields or not. Defaults to False.

        Returns:
            list[tuple[str, str, FieldInfo]]: A list of the fields that are still needed.
                In the format [(field, plugin_name, info), ...]
        """

        # grab args and initialize basic settings
        self.init_settings()

        # initialize the LLMs
        self.init_llms()

        # load plugins
        if hasattr(self, "plugin_flow") is False and self.basic_settings.help:
            logger.debug("Help flag is set and no plugin_flow found. Exiting load method.")
            return None

        self.registry = Registry(self.plugin_flow, plugin_dir=self.basic_settings.plugin_dir)

        # if we want to retreive all fields, we need to load all plugins
        # this is used for help mode
        if all_fields:
            needed_args = []
            for item in self.registry.active_plugins:
                model = item.config
                if model is None:
                    continue
                else:
                    fields = [(name, item.name, info) for name, info in model.model_fields.items()]
                    needed_args.extend(fields)
            return needed_args
        else:
            conf = self.module_settings
            still_needed = self.registry.load_active_plugins(conf)
            return still_needed

    @logger.catch(reraise=True)
    def init_settings(self, load_modules: bool = True) -> None:
        """Initialize the opsbox.settings for the application.
        Will grab the configuration arguments from the environment, command line, or configuration file.

        Sets the `basic_settings`, `plugin_flow`, and `module_settings` attributes.

        Args:
            load_modules (bool): Whether to load the modules or not. Defaults to True.
        """
        # don't repeat yourself
        if all([hasattr(self, "basic_settings"), hasattr(self, "plugin_flow"), hasattr(self, "module_settings")]):
            logger.trace("Using cached settings.")
            return
        else:
            logger.trace("No cache created. Initializing settings.")

        # grab arguments from environment, command line, or config fils
        conf, flow = self._grab_args()

        # set the modules, if specified
        try:
            conf["modules"] = flow.all_visible_modules
            self.plugin_flow = flow  # set the plugin flow
        except AttributeError:
            if not load_modules or conf.get("help", False):
                conf["modules"] = "help_mode"
                logger.trace("Setting modules to help mode.")
                pass
            else:
                raise ValueError("No modules specified in configuration.")

        # set the application settings, plugin flow, and module settings
        self.basic_settings = ApplicationSettings(**conf)
        self.llm_settings = LLMValidator(**conf)
        self.module_settings = conf
        logger.debug("Settings initialized.")

    @logger.catch(reraise=True)
    def grab_conf_environment_plugins(self) -> list[tuple[str, str]] | None:
        """Fetch the available plugins for this configuration evironment.

        Returns:
            list[tuple[str, str, str]] | None: A list of the available plugins.
                In the format [(plugin_name, plugin_type, plugin_uses), ...]
        """
        # initialize basic settings
        self.init_settings()
        flow = PluginFlow()  # dummy flow

        # load the plugins available for this environment
        temp_registry = Registry(flow, plugin_dir=self.basic_settings.plugin_dir)
        return [(plugin.name, plugin.type) for plugin in temp_registry.available_plugins]

    # region Indexing magic methods
    def __getitem__(self, key: str | list[str]) -> any:
        """Get the value of a configuration parameter.

        Args:
            key (str): The key of the parameter to get.

        Returns:
            any: The value of the parameter.
        """
        if isinstance(key, str):
            return getattr(self, key)
        else:
            return {k: getattr(self, k) for k in key}

    def __setitem__(self, key: str, value: any) -> None:
        """Set the value of a configuration parameter.

        Args:
            key (str): The key of the parameter to set.
            value (any): The value to set the parameter to.
        """
        setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        """Delete a configuration parameter.

        Args:
            key (str): The key of the parameter to delete.
        """
        delattr(self, key)
