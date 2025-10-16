import json
import os
from typing import Any

import torch
from loguru import logger
from transformers import (
    AutoModelForCausalLM,
    AutoProcessor,
)

from src.utils.config import Config


class ModelManager:
    """管理多个模型的加载和切换"""

    def __init__(self, config_path: str = "model_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.current_model_key = self.config.get("default_model", "qwen3-4b-fp8")
        self.models = {}
        self.processors = {}
        # 加载全局配置以获取 CUDA 设置
        self.global_config = Config().get_config()
        self.default_device = self.global_config.get("cuda", {}).get("default_device", "auto")

    def _load_config(self) -> dict[str, Any]:
        """加载模型配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        else:
            # 默认配置
            return {"models": {"qwen3-4b-fp8": {"id": "Qwen/Qwen3-4B-Instruct-2507-FP8", "name": "Qwen3 4B FP8 (本地)", "type": "text", "model_class": "AutoModelForCausalLM", "device_map": "auto"}}, "default_model": "qwen3-4b-fp8"}

    def get_available_models(self) -> dict[str, dict[str, Any]]:
        """获取所有可用的模型配置"""
        return self.config["models"]

    def get_current_model_info(self) -> dict[str, Any]:
        """获取当前模型信息"""
        return self.config["models"].get(self.current_model_key, {})

    def load_model(self, model_key: str | None = None) -> bool:
        """加载指定的模型"""
        if model_key is None:
            model_key = self.current_model_key

        if model_key not in self.config["models"]:
            logger.error(f"模型 '{model_key}' 未在配置中找到")
            return False

        # 如果模型已经加载，直接返回
        if model_key in self.models:
            self.current_model_key = model_key
            return True

        model_config = self.config["models"][model_key]
        model_id = model_config["id"]

        try:
            logger.info(f"正在加载模型: {model_config['name']} ({model_id})")

            # 加载processor
            processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True, use_fast=False)
            self.processors[model_key] = processor

            # 根据配置选择模型类
            model_class = AutoModelForCausalLM  # 目前只支持文本模型

            # 准备加载参数
            load_kwargs = {
                "trust_remote_code": True,
            }

            if "device_map" in model_config:
                # 模型配置中指定了 device_map
                device_map = model_config["device_map"]
                if device_map == "auto":
                    # 如果模型配置是 auto，使用全局配置的默认设备
                    load_kwargs["device_map"] = self.default_device
                else:
                    load_kwargs["device_map"] = device_map
            else:
                # 模型配置中没有指定，使用全局配置的默认设备
                load_kwargs["device_map"] = self.default_device

            if "dtype" in model_config:
                load_kwargs["dtype"] = getattr(torch, model_config["dtype"])

            # 加载模型
            model = model_class.from_pretrained(model_id, **load_kwargs)
            model.eval()

            self.models[model_key] = model
            self.current_model_key = model_key

            logger.info(f"模型 '{model_config['name']}' 加载成功!")
            return True

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False

    def get_current_model(self):
        """获取当前加载的模型"""
        if self.current_model_key in self.models:
            return self.models[self.current_model_key]
        return None

    def get_current_processor(self):
        """获取当前模型的处理器"""
        if self.current_model_key in self.processors:
            return self.processors[self.current_model_key]
        return None

    def switch_model(self, model_key: str) -> bool:
        """切换到指定的模型"""
        if model_key not in self.config["models"]:
            logger.error(f"模型 '{model_key}' 未在配置中找到")
            return False

        if model_key not in self.models:
            return self.load_model(model_key)
        else:
            self.current_model_key = model_key
            logger.info(f"已切换到模型: {self.config['models'][model_key]['name']}")
            return True

    def unload_model(self, model_key: str) -> bool:
        """卸载指定的模型以释放内存"""
        if model_key in self.models:
            del self.models[model_key]
        if model_key in self.processors:
            del self.processors[model_key]

        # 清理GPU内存
        torch.cuda.empty_cache()
        logger.info(f"模型 '{model_key}' 已卸载")
        return True

    def reload_config(self):
        """重新加载配置文件"""
        self.config = self._load_config()


# 全局模型管理器实例
model_manager = ModelManager()
