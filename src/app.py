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

    # Launch the Gradio interface with better signal handling
    import atexit
    import signal
    import sys

    def cleanup():
        """清理函数,确保服务器正确关闭"""
        try:
            logger.info("Closing Gradio server...")
            gradio_demo.close()
            logger.info("Gradio server closed successfully")
        except Exception as e:
            logger.error(f"Error closing server: {e}")

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down gracefully...")
        cleanup()
        sys.exit(0)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 注册退出时的清理函数
    atexit.register(cleanup)

    # 启动 Gradio
    launch_kwargs = {
        "mcp_server": False,
        "ssr_mode": False,
        "show_error": True,
        "server_name": server_host,
        "prevent_thread_lock": False,
        "share": False,
        "quiet": False,
    }

    try:
        gradio_demo.queue(max_size=50).launch(server_port=server_port, **launch_kwargs)
        logger.info(f"Gradio interface launched on {server_host}:{server_port}")
    except OSError as e:
        if "Cannot find empty port" in str(e) or "Address already in use" in str(e):
            logger.warning(f"Port {server_port} occupied, trying {server_port + 1}")
            gradio_demo.queue(max_size=50).launch(server_port=server_port + 1, **launch_kwargs)
            logger.info(f"Gradio interface launched on {server_host}:{server_port + 1}")
        else:
            raise
