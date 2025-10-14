"""
文本生成功能模块
"""

import time
from threading import Thread
from typing import Any
import torch
from transformers import TextIteratorStreamer
from loguru import logger
from ..model_manager import model_manager
from .online_client import online_client, is_online_model, get_online_model_id


# @spaces.GPU  # 暂时注释掉装饰器
def generate_text(text: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """纯文本生成函数，支持本地和在线模型"""
    current_model_key = model_manager.current_model_key

    # 检查是否为在线模型
    if is_online_model(current_model_key):
        return _generate_text_online(
            text, current_model_key, max_new_tokens, temperature, top_p, top_k, repetition_penalty
        )
    else:
        return _generate_text_local(
            text, max_new_tokens, temperature, top_p, top_k, repetition_penalty
        )


def _generate_text_local(text: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """本地模型文本生成"""
    current_model = model_manager.get_current_model()
    current_processor = model_manager.get_current_processor()

    if current_model is None or current_processor is None:
        yield "模型未加载", "模型未加载"
        return

    try:
        # 构建消息
        messages = [{"role": "user", "content": text}]
        prompt_full = current_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = current_processor(text=[prompt_full], return_tensors="pt", padding=True).to(next(current_model.parameters()).device)

        streamer = TextIteratorStreamer(current_processor, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens,
            "do_sample": True,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty
        }

        thread = Thread(target=current_model.generate, kwargs=generation_kwargs)
        thread.start()

        buffer = ""
        for new_text in streamer:
            buffer += new_text
            time.sleep(0.01)
            yield buffer, buffer

    except Exception as e:
        logger.error(f"本地文本生成出错: {str(e)}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


def _generate_text_online(text: str, model_key: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """在线模型文本生成"""
    try:
        model_id = get_online_model_id(model_key)
        logger.info(f"使用在线模型生成: {model_id}")

        # 构建生成参数
        params = {
            "max_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty
        }

        # 使用流式生成
        buffer = ""
        for chunk in online_client.stream_generate_text(model_id, text, **params):
            if chunk:
                buffer += chunk
                yield buffer, buffer

    except Exception as e:
        logger.error(f"在线文本生成出错: {str(e)}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


def switch_model(model_key: str) -> str:
    """切换模型，支持本地和在线模型"""
    if is_online_model(model_key):
        # 在线模型切换
        try:
            model_id = get_online_model_id(model_key)
            model_info = online_client.get_model_info(model_id)
            model_name = model_info.get("name", model_id) if model_info else model_id

            # 更新当前模型key（不实际加载模型）
            model_manager.current_model_key = model_key

            logger.info(f"已切换到在线模型: {model_name}")
            return f"已切换到在线模型: {model_name}"
        except Exception as e:
            logger.error(f"在线模型切换失败: {e}")
            return f"在线模型切换失败: {str(e)}"
    else:
        # 本地模型切换
        if model_manager.switch_model(model_key):
            model_info = model_manager.get_current_model_info()
            logger.info(f"已切换到本地模型: {model_info.get('name', 'Unknown')}")
            return f"已切换到本地模型: {model_info.get('name', 'Unknown')}"
        else:
            logger.error("本地模型切换失败")
            return "模型切换失败"


def connect_to_online_server(server_url: str) -> dict:
    """连接到在线服务器"""
    from .online_client import connect_to_server
    return connect_to_server(server_url)