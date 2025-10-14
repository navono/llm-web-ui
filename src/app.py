from .utils import Config, CustomizeLogger

gen_config = Config().get_config()
logger = CustomizeLogger.make_logger(gen_config["log"])


async def start():
    logger.info("Hello from py-project-template!")
