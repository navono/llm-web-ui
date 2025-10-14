from .gradio import create_interface as demo
from .utils import Config, CustomizeLogger

gen_config = Config().get_config()
logger = CustomizeLogger.make_logger(gen_config["log"])


async def start():
    """Start the LLM web UI application."""
    logger.info("Starting LLM Web UI with multi-model interface...")

    # 从配置文件获取端口设置
    http_config = gen_config.get("http", {})
    server_host = http_config.get("host", "0.0.0.0")
    server_port = http_config.get("port", 7861)

    logger.info(f"Starting server on {server_host}:{server_port}")

    # 创建 Gradio 界面
    gradio_demo = demo()

    # Launch the Gradio interface
    gradio_demo.queue(max_size=50).launch(
        mcp_server=False,
        ssr_mode=False,
        show_error=True,
        server_name=server_host,
        server_port=server_port
    )

    logger.info(f"Gradio interface launched successfully on {server_host}:{server_port}!")
