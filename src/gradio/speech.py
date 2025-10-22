"""
Speech-to-Text 和 Text-to-Speech 功能实现
使用兼容 OpenAI API 的方式接入服务
"""

import os
import tempfile

from loguru import logger

import gradio as gr

from .online_client import get_online_model_id, is_online_model, online_client


def get_available_voices() -> dict:
    """
    从在线服务器获取可用的声音列表

    Returns:
        dict: 包含 success 和 voices/error 的字典
    """
    try:
        # 检查是否为在线模型
        if not is_online_model(online_client.model_id):
            return {"success": False, "error": "需要连接到在线服务器"}

        # 尝试调用 /v1/tts/voices 端点
        url = f"{online_client.base_url}/tts/voices"
        logger.info(f"获取声音列表: {url}")

        response = online_client.session.get(url, timeout=10)

        if response.status_code == 200:
            result = response.json()
            # 解析返回的声音列表
            voices = []

            # 处理不同的返回格式
            if "audio_files" in result and isinstance(result["audio_files"], dict):
                # IndexTTS 格式: {"audio_files": {"0": "file1.wav", "1": "file2.wav"}}
                voices = list(result["audio_files"].values())
            elif "voices" in result:
                # 标准格式: {"voices": ["voice1", "voice2"]}
                voices = result["voices"]
            elif "data" in result:
                # OpenAI 格式: {"data": [{"id": "voice1"}, {"id": "voice2"}]}
                voices = [v.get("id", v.get("name", str(v))) for v in result["data"]]

            # 添加标准 OpenAI 声音
            standard_voices = []
            all_voices = standard_voices + [v for v in voices if v not in standard_voices]

            logger.info(f"获取到 {len(all_voices)} 个声音")
            return {"success": True, "voices": all_voices}
        else:
            # 如果端点不存在，返回默认声音列表
            logger.warning(f"无法获取声音列表 (HTTP {response.status_code})，使用默认列表")
            default_voices = []
            return {"success": True, "voices": default_voices}

    except Exception as e:
        logger.error(f"获取声音列表异常: {str(e)}", exc_info=True)
        # 返回默认声音列表
        default_voices = []
        return {"success": True, "voices": default_voices}


def generate_speech_to_text(audio_path: str) -> tuple[str, str]:
    """
    语音转文字功能，使用 OpenAI 兼容的 API
    直接使用 online_client 的服务地址（即用户在 UI 中输入的服务器地址）

    Args:
        audio_path: 音频文件路径

    Returns:
        Tuple[str, str]: (原始输出, Markdown格式输出)
    """
    if not audio_path:
        error_msg = "请先上传或录制音频文件"
        gr.Warning(error_msg)
        return error_msg, f"**Error:** {error_msg}"

    try:
        # 使用 online_client 的服务地址进行 STT
        model_id = "whisper-1"
        logger.info(f"使用服务地址 {online_client.base_url} 进行语音转文字, 模型: {model_id}, 音频文件: {audio_path}")

        # 调用 OpenAI 兼容的 /audio/transcriptions 端点
        result = transcribe_audio(audio_path, model_id)

        if result.get("success"):
            transcription = result.get("text", "")
            logger.info(f"转录成功，文本长度: {len(transcription)}")
            gr.Info("语音转文字成功")
            return transcription, f"## 转录结果\n\n{transcription}"
        else:
            error_msg = result.get("error", "语音转文字处理失败")
            logger.error(f"转录失败: {error_msg}")
            gr.Error(f"转录失败: {error_msg}")
            return f"Error: {error_msg}", f"**Error:** {error_msg}"

    except Exception as e:
        logger.error(f"语音转文字处理异常: {str(e)}", exc_info=True)
        error_msg = f"处理失败: {str(e)}"
        gr.Error(error_msg)
        return error_msg, f"**Error:** {error_msg}"


def transcribe_audio(audio_path: str, model: str = "whisper-1") -> dict:
    """
    使用 OpenAI 兼容的 API 进行音频转录
    使用 online_client 的服务地址（即用户在 UI 中输入的服务器地址）

    Args:
        audio_path: 音频文件路径
        model: 模型名称，默认为 whisper-1

    Returns:
        dict: 包含 success 和 text/error 的字典
    """
    try:
        # 打开音频文件
        with open(audio_path, "rb") as audio_file:
            # 准备 multipart/form-data 请求
            files = {"file": (os.path.basename(audio_path), audio_file, "audio/mpeg")}
            data = {"model": model}

            # 调用 OpenAI 兼容的 /audio/transcriptions 端点
            url = f"{online_client.base_url}/audio/transcriptions"
            logger.info(f"发送转录请求到: {url}")

            # 临时移除 Content-Type header，让 requests 自动设置 multipart/form-data
            original_headers = online_client.session.headers.copy()
            if "Content-Type" in online_client.session.headers:
                del online_client.session.headers["Content-Type"]

            response = online_client.session.post(url, files=files, data=data, timeout=120)

            # 恢复原始 headers
            online_client.session.headers.update(original_headers)

            if response.status_code == 200:
                result = response.json()
                # OpenAI API 返回格式: {"text": "转录文本"}
                if "text" in result:
                    return {"success": True, "text": result["text"]}
                else:
                    return {"success": False, "error": "响应格式错误，缺少 text 字段"}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"转录请求失败: {error_msg}")
                return {"success": False, "error": error_msg}

    except FileNotFoundError:
        error_msg = f"音频文件不存在: {audio_path}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"转录异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}


def generate_text_to_speech(text: str, voice: str = "alloy", speed: float = 1.0) -> tuple[str | None, str]:
    """
    文字转语音功能，使用 OpenAI 兼容的 API

    Args:
        text: 要转换的文本
        voice: 语音类型 (alloy, echo, fable, onyx, nova, shimmer)
        speed: 语速 (0.25 - 4.0)

    Returns:
        tuple[str | None, str]: (音频文件路径或None, 状态消息)
    """
    if not text or not text.strip():
        error_msg = "请输入要转换的文本"
        gr.Warning(error_msg)
        return None, f"**Error:** {error_msg}"

    try:
        from ..model_manager import model_manager

        current_model_key = model_manager.current_model_key

        # 检查是否为在线模型
        if not is_online_model(current_model_key):
            error_msg = "文字转语音功能仅支持在线模型，请先连接到在线服务器并选择模型"
            gr.Error(error_msg)
            return None, f"**Error:** {error_msg}"

        # 获取实际的模型ID
        model_id = get_online_model_id(current_model_key)
        logger.info(f"使用在线模型进行文字转语音: {model_id}, 文本长度: {len(text)}")

        # 调用 OpenAI 兼容的 /audio/speech 端点
        result = synthesize_speech(text, model_id, voice, speed)

        if result.get("success"):
            audio_path = result.get("audio_path")
            logger.info(f"语音合成成功，音频文件: {audio_path}")
            gr.Info("语音合成成功")
            return audio_path, f"## 语音合成成功\n\n文本长度: {len(text)} 字符"
        else:
            error_msg = result.get("error", "文字转语音处理失败")
            logger.error(f"语音合成失败: {error_msg}")
            gr.Error(f"语音合成失败: {error_msg}")
            return None, f"**Error:** {error_msg}"

    except Exception as e:
        logger.error(f"文字转语音处理异常: {str(e)}", exc_info=True)
        error_msg = f"处理失败: {str(e)}"
        gr.Error(error_msg)
        return None, f"**Error:** {error_msg}"


def synthesize_speech(text: str, model: str = "tts-1", voice: str = "alloy", speed: float = 1.0) -> dict:
    """
    使用 OpenAI 兼容的 API 进行语音合成

    Args:
        text: 要转换的文本
        model: 模型名称，默认为 tts-1
        voice: 语音类型
        speed: 语速

    Returns:
        dict: 包含 success 和 audio_path/error 的字典
    """
    try:
        # 准备请求数据
        payload = {"model": model, "input": text, "voice": voice, "speed": speed}

        # 调用 OpenAI 兼容的 /audio/speech 端点
        url = f"{online_client.base_url}/audio/speech"
        logger.info(f"发送语音合成请求到: {url}")

        response = online_client.session.post(url, json=payload, timeout=120)

        if response.status_code == 200:
            # 保存音频文件到临时目录
            temp_dir = tempfile.gettempdir()
            audio_filename = f"tts_{os.urandom(8).hex()}.mp3"
            audio_path = os.path.join(temp_dir, audio_filename)

            with open(audio_path, "wb") as f:
                f.write(response.content)

            logger.info(f"音频文件已保存到: {audio_path}")
            return {"success": True, "audio_path": audio_path}
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"语音合成请求失败: {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"语音合成异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}
