from .gradio import demo
from .utils import Config, CustomizeLogger

gen_config = Config().get_config()
logger = CustomizeLogger.make_logger(gen_config["log"])


async def start():
    """Start the LLM web UI application."""
    logger.info("Starting LLM Web UI with multi-model interface...")

    # Launch the Gradio interface
    demo.queue(max_size=50).launch(mcp_server=False, ssr_mode=False, show_error=True, server_name="0.0.0.0", server_port=7861)

    logger.info("Gradio interface launched successfully!")
