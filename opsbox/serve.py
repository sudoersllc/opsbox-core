from copy import deepcopy
import logging
import traceback
from mcp.server import FastMCP
from config import Config2, find_missing_fields
from loguru import logger
from opsbox.plugins import Result, PluginInfo, Registry
from opsbox.main import start_logging

from mcp.server.session import ServerSession

# Intercept standard logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0)

####################################################################################
# Temporary monkeypatch which avoids crashing when a POST message is received
# before a connection has been initialized, e.g: after a deployment.
# pylint: disable-next=protected-access
old__received_request = ServerSession._received_request


async def _received_request(self, *args, **kwargs):
    try:
        return await old__received_request(self, *args, **kwargs)
    except RuntimeError:
        pass


# pylint: disable-next=protected-access
ServerSession._received_request = _received_request
####################################################################################

mcp1 = FastMCP()
@logger.catch(reraise=True)
def generate_tools():
    config = Config2()
    config.load_env_config()
    reg = Registry(plugin_dir=config.basic_settings.plugin_dir)

    available_plugins = [plugin for plugin in reg.available_plugins if plugin.type not in ["handler", "provider", "output"]]
    truly_available_plugins = []
    for plugin in available_plugins:
        result = find_missing_fields([plugin.plugin_obj], config.module_settings)
        if len(result) == 0 and plugin.name not in [item.name for item in truly_available_plugins]:
            truly_available_plugins.append(plugin)

    truly_available_plugins = [plugin for plugin in truly_available_plugins if plugin.type not in ["handler", "provider", "output"]]
    active = reg.active_plugins([plugin.name for plugin in truly_available_plugins])
    reg.load_multiple_plugins(active, config.module_settings)

    def gen_tool(plugin, active):
        handler = reg.handlers[plugin.type]
        logger.info(f"Generating tool for {plugin.name} with type {plugin.type}")
        def tool_func():
            try:
                logger.info(f"Calling {plugin.name} with type {plugin.type}")
                result = handler.process_plugin(plugin, [], active)
                return result.formatted
            except Exception as e:
                logger.error(f"Error in {plugin.name}: {traceback.format_exc()}")   
                return traceback.format_exc()
        
        return tool_func
    
    for plugin in truly_available_plugins:
        mcp1.add_tool(
            gen_tool(plugin, active),
            name=plugin.name,
            description="A tool for " + plugin.name,
        )
    pass

def build():
    start_logging(log_level="TRACE", log_file="logue.log")
    generate_tools()
    #mcp1.run("sse")
    mcp1.run()
    
if __name__ == "__main__":
    build()

