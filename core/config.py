from pydantic import BaseModel, Field, ValidationError
from pydantic.fields import FieldInfo
import sys
from .plugins import Registry, PluginFlow
from core.utils import SingletonMeta
from os import environ, path
import json


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


class EssentialSettings(BaseModel):
    """The class is used to store the essential settings for the application.
    The essential settings are the settings that are required to run the application.
    """

    modules: list[str] | str = Field(..., description="List of modules to load", required=True)
    config: str | None = Field(
        default=find_config_file(".opsbox_conf.json"), description="Path to the configuration file", required=False
    )
    plugin_dir: str | None = Field(None, description="The directory to load plugins from", required=False)


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
    """

    def _load_config_file(self, config_file: str) -> dict:
        """Loads the configuration from a configuration file.

        Args:
            config_file (str): The path to the configuration file.
        """
        with open(config_file, "r") as file:
            json_conf = json.load(file)
            return json_conf

    def _parse_cmd_arguments(self) -> dict:
        """Parse the command line arguments and return them as a dictionary.
        Can handle both --arg=value and --arg value formats.

        Returns:
            dict: The command line arguments in {arg: value} format.
        """
        logger.debug(f"Parsing {len(sys.argv)-1} command line arguments...")

        def convert_to_numeric(value):
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value

        args = sys.argv[1:]  # Skip the script name
        arg_labels = [(index, arg) for index, arg in enumerate(args) if arg.startswith("--")]

        if "=" in arg_labels[0][1]:
            arg_dict = {
                label.split("=")[0].strip("-"): convert_to_numeric(label.split("=")[1]) for index, label in arg_labels
            }
        else:
            arg_dict = {label.strip("-"): convert_to_numeric(args[index + 1]) for index, label in arg_labels}

        return arg_dict

    def _grab_args(self) -> tuple[dict, PluginFlow]:
        """Grab the configuration arguments from the environment, command line, or configuration file.

        Returns:
            tuple[dict, PluginFlow]: The configuration arguments and the plugin flow."""
        logger.debug("Grabbing configuration arguments...")
        conf = {}  # default config

        # if arguments are specified in command line, load them
        if len(sys.argv) > 1:
            conf.update(self._parse_cmd_arguments())

        # if default config file is set, load args from it
        default_config_file = find_config_file(".opsbox.json")
        if default_config_file is not None:
            try:
                conf = self._load_config_file(default_config_file)
                logger.debug(f"Loaded default config file {default_config_file}")
            except FileNotFoundError:
                logger.debug("No default config file found. Falling back...")
            except json.JSONDecodeError:
                logger.warning("Default config file is not valid JSON. Consider fixing that! Falling back...")

        # if config file is specified in command line, load args from it
        if "config" in conf:
            config_path = conf["config"]
            logger.debug(f"Loading module pipeline from config file {config_path}")
            conf.update(self._load_config_file(config_path))
        else:
            logger.debug("No config file specified in command line. Falling back...")

        lower_case_environ = {key.lower(): value for key, value in environ.items()}
        conf.update(lower_case_environ)  # load any environment variables

        # set the pipeline
        if "modules" in conf:
            pipeline = PluginFlow().set_flow(conf["modules"])
        else:
            logger.critical("No module pipeline specified. Exiting...")
            sys.exit(1)

        return conf, pipeline

    def load(self) -> None | list[tuple[str, str, FieldInfo]]:
        """Bootstraps the configuration code and argument parsing.

        This method is used to load the configuration data from the command line, environment variables,
        or a configuration file.

        Returns:
            list[tuple[str, str, FieldInfo]]: A list of the fields that are still needed.
                In the format [(field, plugin_name, info), ...]"""

        # grab args and initialize basic settings
        conf, flow = self._grab_args()
        print(conf)
        conf["modules"] = flow.all_modules
        self.basic_settings = EssentialSettings(**conf)
        self.llm_settings = LLMValidator(**conf)
        self.module_settings = conf

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

        # load plugins
        self.registry = Registry(flow, plugin_dir=self.basic_settings.plugin_dir)
        still_needed = []
        for item in self.registry.active_plugins:
            try:
                self.registry.load(conf, item)
            except ValidationError:  # collect missing fields
                model = item.config
                if model is None:
                    continue
                else:
                    needed = [
                        (name, item.name, info)
                        for name, info in model.model_fields.items()
                        if (name not in conf) and (info.is_required)
                    ]
                    still_needed.extend(needed)
                continue
        if len(still_needed) > 0:
            return still_needed

    @logger.catch(reraise=True)
    def load_help(self) -> list[tuple[str, str, FieldInfo]]:
        """Load the help for the configuration."""
        # grab args and initialize basic settings
        conf, flow = self._grab_args()
        conf["modules"] = flow.all_modules
        self.basic_settings = EssentialSettings(**conf)
        self.module_settings = conf

        # load plugins
        self.registry = Registry(flow, plugin_dir=self.basic_settings.plugin_dir)
        needed_args = []
        for item in self.registry.active_plugins:
            model = item.config
            if model is None:
                continue
            else:
                needed = [
                    (name, item.name, info)
                    for name, info in model.model_fields.items()
                    if (name not in conf) and (info.is_required)
                ]
                needed_args.extend(needed)

        return needed_args

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
