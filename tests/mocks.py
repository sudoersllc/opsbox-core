import json
from opsbox.plugins import PluginInfo, Registry, PluginFlow
import opsbox.config as config
from typing import Any
import contextlib


def MockPlugin(
    input_class: type,
    plugin_type: str,
    data: dict | None = None,
    uses: list[str] | None = None,
    extra: dict[str, Any] | None = None,
    appconfig: config.AppConfig | None = None,
) -> PluginInfo:
    """Produce a mock plugin with a given name."""

    plugin_obj = input_class()

    with contextlib.suppress(AttributeError):
        config_model = plugin_obj.grab_config()

        if config_model and appconfig:
            module_settings = appconfig.module_settings
            print(module_settings)
            plugin_conf = config_model(**module_settings)
            plugin_obj.set_data(plugin_conf)

    if data:
        plugin_obj.set_data(data)

    if not config_model:
        config_model = None

    plugin = PluginInfo(
        name=input_class.__name__,
        module=input_class.__module__,
        class_name=input_class.__name__,
        toml_path="",
        type=plugin_type,
        plugin_obj=plugin_obj,
        config=config_model,
        uses=uses,
        extra=extra,
    )
    return plugin


def MockConfig(path: str | None, override: dict | None = None, use_home: bool = False) -> config.AppConfig:
    """Create a mock config for testing purposes.

    Args:
        path (str | None): The path to the config file to load.
        override (dict): The dictionary of settings to override.
        use_home (bool): Whether to use the home config file or not. Defaults to False.
    """
    # clear singleton
    appconfig = config.AppConfig()
    with contextlib.suppress(AttributeError):
        del appconfig._instance

    # get the config from the file
    if path is not None:
        with open(path, "r") as f:
            item: dict = json.load(f)
            print(item)

    if use_home:
        path_home = config.find_config_file("config.json")
        with open(path_home, "r") as f:
            item.update(json.load(f))

    # combine the two dictionaries
    item = {**item, **override} if override is not None else item

    conf = config.AppConfig()
    conf.basic_settings = config.EssentialSettings(**item, path=path)
    conf.module_settings = item
    return conf


def MockRegistry(plugins: list[PluginInfo], flow: PluginFlow, plugin_dir=str | None) -> Registry:
    """Create a mock registry for testing purposes.

    Args:
        plugins (list[PluginInfo]): The list of plugins to use.
        plugin_dir (str): The directory to use for the plugins.
    """
    # clear singleton
    Registry._instance = None

    item = Registry(flow=flow, plugin_dir=plugin_dir)
    setattr(item, "active_plugins", plugins)
    return item
