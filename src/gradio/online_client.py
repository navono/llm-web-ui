"""
Online模式客户端模块
用于连接远程服务端并获取模型列表
"""

import json
from typing import Any

import requests
from loguru import logger


class OnlineClient:
    """Online模式客户端，用于连接远程服务端"""

    def __init__(self, base_url: str = "http://localhost:8080/v1"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    def test_connection(self) -> bool:
        """测试与服务端的连接"""
        try:
            # 尝试 OpenAI 兼容的端点
            response = self.session.get(f"{self.base_url}/models", timeout=5)
            if response.status_code == 200:
                return True

            # 尝试自定义端点
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False

    def get_available_models(self) -> list[dict[str, Any]]:
        """获取服务端可用模型列表"""
        try:
            # 尝试 OpenAI 兼容的 /models 端点
            response = self.session.get(f"{self.base_url}/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = []

                if isinstance(data, dict) and "data" in data:
                    # OpenAI 兼容格式
                    for model in data["data"]:
                        models.append({"id": model.get("id", "unknown"), "name": model.get("id", "unknown"), "object": model.get("object", "model")})
                elif isinstance(data, list):
                    # 直接是模型列表
                    for model in data:
                        if isinstance(model, dict):
                            models.append({"id": model.get("id", model.get("name", "unknown")), "name": model.get("name", model.get("id", "unknown")), "object": model.get("object", "model")})
                        else:
                            models.append({"id": str(model), "name": str(model), "object": "model"})

                logger.info(f"成功获取 {len(models)} 个远程模型")
                return models
            else:
                # 尝试自定义端点
                response = self.session.get(f"{self.base_url}/api/models", timeout=10)
                if response.status_code == 200:
                    models = response.json()
                    logger.info(f"成功获取 {len(models)} 个远程模型")
                    return models
                else:
                    logger.error(f"获取模型列表失败: HTTP {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"获取模型列表异常: {e}")
            return []

    def generate_text(self, model_id: str, prompt_or_messages, **kwargs) -> str:
        """使用远程模型生成文本"""
        try:
            # 判断输入是消息数组还是文本提示
            if isinstance(prompt_or_messages, list):
                # 已经是消息数组格式（多模态）
                messages = prompt_or_messages
            else:
                # 简单文本提示，转换为消息格式
                messages = [{"role": "user", "content": prompt_or_messages}]

            # 尝试 OpenAI 兼容格式
            payload = {"model": model_id, "messages": messages, **kwargs}

            # 转换参数名
            if "max_new_tokens" in kwargs:
                payload["max_tokens"] = kwargs.pop("max_new_tokens")

            response = self.session.post(f"{self.base_url}/chat/completions", json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]
                elif "text" in data:
                    return data["text"]
                else:
                    return "响应格式未知"
            else:
                # 尝试自定义端点
                # 对于多模态消息，需要提取文本内容
                if isinstance(messages, list) and len(messages) > 0:
                    # 多模态消息，提取文本内容
                    content = ""
                    for msg in messages:
                        if isinstance(msg["content"], list):
                            for item in msg["content"]:
                                if item.get("type") == "text":
                                    content += item.get("text", "")
                        elif isinstance(msg["content"], str):
                            content += msg["content"]
                    prompt = content
                else:
                    prompt = str(messages)

                payload = {"model": model_id, "prompt": prompt, **kwargs}
                response = self.session.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
                if response.status_code == 200:
                    return response.json().get("text", "")
                else:
                    logger.error(f"文本生成失败: HTTP {response.status_code}")
                    return f"生成失败: HTTP {response.status_code}"
        except Exception as e:
            logger.error(f"文本生成异常: {e}")
            return f"生成异常: {str(e)}"

    def stream_generate_text(self, model_id: str, prompt_or_messages, **kwargs):
        """流式文本生成"""
        try:
            # 判断输入是消息数组还是文本提示
            if isinstance(prompt_or_messages, list):
                # 已经是消息数组格式（多模态）
                messages = prompt_or_messages
            else:
                # 简单文本提示，转换为消息格式
                messages = [{"role": "user", "content": prompt_or_messages}]

            # 尝试 OpenAI 兼容格式
            payload = {"model": model_id, "messages": messages, "stream": True, **kwargs}

            # 转换参数名
            if "max_new_tokens" in kwargs:
                payload["max_tokens"] = kwargs.pop("max_new_tokens")

            response = self.session.post(f"{self.base_url}/chat/completions", json=payload, stream=True, timeout=120)

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            line_str = line.decode("utf-8")
                            if line_str.startswith("data: "):
                                line_str = line_str[6:]  # 移除 'data: ' 前缀

                            if line_str == "[DONE]":
                                break

                            data = json.loads(line_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                            elif "text" in data:
                                yield data["text"]
                        except json.JSONDecodeError:
                            continue
            else:
                # 尝试自定义端点
                # 对于多模态消息，需要提取文本内容
                if isinstance(messages, list) and len(messages) > 0:
                    # 多模态消息，提取文本内容
                    content = ""
                    for msg in messages:
                        if isinstance(msg["content"], list):
                            for item in msg["content"]:
                                if item.get("type") == "text":
                                    content += item.get("text", "")
                        elif isinstance(msg["content"], str):
                            content += msg["content"]
                    prompt = content
                else:
                    prompt = str(messages)

                payload = {"model": model_id, "prompt": prompt, "stream": True, **kwargs}
                response = self.session.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=120)
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode("utf-8"))
                                if "text" in data:
                                    yield data["text"]
                            except json.JSONDecodeError:
                                continue
                else:
                    logger.error(f"流式生成失败: HTTP {response.status_code}")
                    yield f"生成失败: HTTP {response.status_code}"
        except Exception as e:
            logger.error(f"流式生成异常: {e}")
            yield f"生成异常: {str(e)}"

    def get_model_info(self, model_id: str) -> dict[str, Any] | None:
        """获取特定模型信息"""
        try:
            response = self.session.get(f"{self.base_url}/api/models/{model_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取模型信息失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取模型信息异常: {e}")
            return None


# 全局online客户端实例
online_client = OnlineClient("http://localhost:8080/v1")


def connect_to_server(server_url: str) -> dict[str, Any]:
    """连接到指定的服务器"""
    global online_client

    try:
        # 更新客户端URL
        online_client.base_url = server_url.rstrip("/")

        # 测试连接
        if online_client.test_connection():
            # 获取模型列表
            models = online_client.get_available_models()

            # 格式化模型选项
            model_choices = []
            for model in models:
                name = model.get("name", model.get("id", "Unknown"))
                model_id = model.get("id", "unknown")
                model_choices.append((f"[Online] {name}", f"online:{model_id}"))

            return {"success": True, "message": f"成功连接到 {server_url}", "models": model_choices, "server_url": server_url}
        else:
            error_msg = f"无法连接到 {server_url}，请检查服务器地址和端口是否正确"
            return {"success": False, "error": error_msg, "message": error_msg, "models": [], "server_url": server_url}
    except Exception as e:
        logger.error(f"连接服务器异常: {e}")
        error_msg = f"连接异常: {str(e)}"
        return {"success": False, "error": error_msg, "message": error_msg, "models": [], "server_url": server_url}


def get_online_model_info(model_key: str) -> dict[str, Any]:
    """获取在线模型信息"""
    if model_key.startswith("online:"):
        model_id = model_key[7:]  # 移除 "online:" 前缀
        return online_client.get_model_info(model_id)
    return {}


def is_online_model(model_key: str) -> bool:
    """检查是否为在线模型"""
    return model_key.startswith("online:")


def get_online_model_id(model_key: str) -> str:
    """获取在线模型的实际ID"""
    if model_key.startswith("online:"):
        return model_key[7:]
    return model_key
