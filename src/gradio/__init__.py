"""
Gradio模块主入口
"""

import os
import torch
from loguru import logger

# 设备配置
device = torch.device("cuda:6" if torch.cuda.is_available() else "cpu")

# 设备信息日志
logger.info(f"CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}")
logger.info(f"torch.__version__={torch.__version__}")
logger.info(f"torch.version.cuda={torch.version.cuda}")
logger.info(f"cuda available={torch.cuda.is_available()}")
logger.info(f"cuda device count={torch.cuda.device_count()}")
if torch.cuda.is_available():
    logger.info(f"current device={torch.cuda.current_device()}")
    logger.info(f"device name={torch.cuda.get_device_name(torch.cuda.current_device())}")
logger.info(f"Using device={device}")

def create_interface():
    """延迟创建界面，避免循环导入"""
    from .ui_components import create_interface as _create_interface
    from ..model_manager import model_manager

    # 初始化模型管理器并加载默认模型
    logger.info("正在初始化模型管理器...")
    if not model_manager.load_model():
        logger.error("默认模型加载失败!")
        exit(1)

    current_model_info = model_manager.get_current_model_info()
    logger.info(f"当前使用模型: {current_model_info.get('name', 'Unknown')}")

    # 创建Gradio界面
    return _create_interface()

__all__ = ['create_interface']