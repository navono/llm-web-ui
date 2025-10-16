"""
多模态生成功能模块
包含图像、视频、PDF、GIF等处理和生成功能
"""

import base64
import time
from io import BytesIO
from threading import Thread
from typing import Any

import cv2
import numpy as np
import torch
from loguru import logger
from PIL import Image
from transformers import TextIteratorStreamer

from ..model_manager import model_manager
from .online_client import get_online_model_id, is_online_model, online_client

# 常量定义
MAX_MAX_NEW_TOKENS = 4096
DEFAULT_MAX_NEW_TOKENS = 1024
device = torch.device("cuda:6" if torch.cuda.is_available() else "cpu")


def extract_gif_frames(gif_path: str):
    """从GIF中提取帧"""
    if not gif_path:
        return []
    with Image.open(gif_path) as gif:
        total_frames = gif.n_frames
        frame_indices = np.linspace(0, total_frames - 1, min(total_frames, 10), dtype=int)
        frames = []
        for i in frame_indices:
            gif.seek(i)
            frames.append(gif.convert("RGB").copy())
    return frames


def downsample_video(video_path):
    """视频降采样"""
    vidcap = cv2.VideoCapture(video_path)
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    frame_indices = np.linspace(0, total_frames - 1, min(total_frames, 10), dtype=int)
    for i in frame_indices:
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, i)
        success, image = vidcap.read()
        if success:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image)
            frames.append(pil_image)
    vidcap.release()
    return frames


def convert_pdf_to_images(file_path: str, dpi: int = 200):
    """PDF转图片"""
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF 未安装，无法处理PDF文件")
        return []

    if not file_path:
        return []
    images = []
    pdf_document = fitz.open(file_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        images.append(Image.open(BytesIO(img_data)))
    pdf_document.close()
    return images


def encode_image_to_base64(image: Image.Image) -> str:
    """将PIL图像编码为base64字符串"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def get_initial_pdf_state() -> dict[str, Any]:
    """获取初始PDF状态"""
    return {"pages": [], "total_pages": 0, "current_page_index": 0}


def load_and_preview_pdf(file_path: str | None) -> tuple[Image.Image | None, dict[str, Any], str]:
    """加载并预览PDF"""
    state = get_initial_pdf_state()
    if not file_path:
        return None, state, '<div style="text-align:center;">No file loaded</div>'
    try:
        pages = convert_pdf_to_images(file_path)
        if not pages:
            return None, state, '<div style="text-align:center;">Could not load file</div>'
        state["pages"] = pages
        state["total_pages"] = len(pages)
        page_info_html = f'<div style="text-align:center;">Page 1 / {state["total_pages"]}</div>'
        return pages[0], state, page_info_html
    except Exception as e:
        logger.error(f"PDF预览失败: {e}")
        return None, state, f'<div style="text-align:center;">Failed to load preview: {e}</div>'


def navigate_pdf_page(direction: str, state: dict[str, Any]):
    """PDF页面导航"""
    if not state or not state["pages"]:
        return None, state, '<div style="text-align:center;">No file loaded</div>'
    current_index = state["current_page_index"]
    total_pages = state["total_pages"]
    if direction == "prev":
        new_index = max(0, current_index - 1)
    elif direction == "next":
        new_index = min(total_pages - 1, current_index + 1)
    else:
        new_index = current_index
    state["current_page_index"] = new_index
    image_preview = state["pages"][new_index]
    page_info_html = f'<div style="text-align:center;">Page {new_index + 1} / {total_pages}</div>'
    return image_preview, state, page_info_html


# @spaces.GPU
def generate_image(text: str, image: Image.Image, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """图像生成函数，支持本地和在线模型"""
    current_model_key = model_manager.current_model_key

    if image is None:
        yield "Please upload an image.", "Please upload an image."
        return

    # 检查是否为在线模型
    if is_online_model(current_model_key):
        # 递归调用在线生成函数
        yield from _generate_image_online(text, image, current_model_key, max_new_tokens, temperature, top_p, top_k, repetition_penalty)
    else:
        # 递归调用本地生成函数
        yield from _generate_image_local(text, image, max_new_tokens, temperature, top_p, top_k, repetition_penalty)


def _generate_image_local(text: str, image: Image.Image, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """本地模型图像生成"""
    current_model = model_manager.get_current_model()
    current_processor = model_manager.get_current_processor()

    if current_model is None or current_processor is None:
        yield "模型未加载", "模型未加载"
        return

    # 检查模型类型
    model_info = model_manager.get_current_model_info()
    if model_info.get("type") != "multimodal":
        yield "当前本地模型不支持图像处理，请切换到多模态模型", "当前本地模型不支持图像处理，请切换到多模态模型"
        return

    try:
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": text}]}]
        prompt_full = current_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = current_processor(text=[prompt_full], images=[image], return_tensors="pt", padding=True).to(device)
        streamer = TextIteratorStreamer(current_processor, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens}
        thread = Thread(target=current_model.generate, kwargs=generation_kwargs)
        thread.start()
        buffer = ""
        for new_text in streamer:
            buffer += new_text
            time.sleep(0.01)
            yield buffer, buffer
    except Exception as e:
        logger.error(f"本地图像生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


def _generate_image_online(text: str, image: Image.Image, model_key: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """在线模型图像生成"""
    try:
        model_id = get_online_model_id(model_key)
        logger.info(f"使用在线模型生成图像: {model_id}")

        # 编码图像为base64
        image_base64 = encode_image_to_base64(image)

        # 构建消息
        messages = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_base64}}, {"type": "text", "text": text}]}]

        # 构建生成参数
        params = {"model": model_id, "messages": messages, "max_tokens": max_new_tokens, "temperature": temperature, "top_p": top_p, "stream": True}

        # 使用流式生成 - 传递结构化的消息而不是JSON字符串
        buffer = ""
        for chunk in online_client.stream_generate_text(model_id, messages, **params):
            if chunk:
                buffer += chunk
                yield buffer, buffer

    except Exception as e:
        logger.error(f"在线图像生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


# @spaces.GPU
def generate_video(text: str, video_path: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """视频生成函数"""
    if video_path is None:
        yield "Please upload a video.", "Please upload a video."
        return

    current_model = model_manager.get_current_model()
    current_processor = model_manager.get_current_processor()

    if current_model is None or current_processor is None:
        yield "模型未加载", "模型未加载"
        return

    # 检查模型类型
    model_info = model_manager.get_current_model_info()
    if model_info.get("type") != "multimodal":
        yield "当前模型不支持视频处理，请切换到多模态模型", "当前模型不支持视频处理，请切换到多模态模型"
        return

    try:
        frames = downsample_video(video_path)
        if not frames:
            yield "Could not process video.", "Could not process video."
            return
        messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        for _frame in frames:
            messages[0]["content"].insert(0, {"type": "image"})
        prompt_full = current_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = current_processor(text=[prompt_full], images=frames, return_tensors="pt", padding=True).to(device)
        streamer = TextIteratorStreamer(current_processor, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens, "do_sample": True, "temperature": temperature, "top_p": top_p, "top_k": top_k, "repetition_penalty": repetition_penalty}
        thread = Thread(target=current_model.generate, kwargs=generation_kwargs)
        thread.start()
        buffer = ""
        for new_text in streamer:
            buffer += new_text
            buffer = buffer.replace("<|im_end|>", "")
            time.sleep(0.01)
            yield buffer, buffer
    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


# @spaces.GPU
def generate_pdf(text: str, state: dict[str, Any], max_new_tokens: int = 2048, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """PDF生成函数"""
    if not state or not state["pages"]:
        yield "Please upload a PDF file first.", "Please upload a PDF file first."
        return

    current_model = model_manager.get_current_model()
    current_processor = model_manager.get_current_processor()

    if current_model is None or current_processor is None:
        yield "模型未加载", "模型未加载"
        return

    # 检查模型类型
    model_info = model_manager.get_current_model_info()
    if model_info.get("type") != "multimodal":
        yield "当前模型不支持PDF处理，请切换到多模态模型", "当前模型不支持PDF处理，请切换到多模态模型"
        return

    try:
        page_images = state["pages"]
        full_response = ""
        for i, image in enumerate(page_images):
            page_header = f"--- Page {i + 1}/{len(page_images)} ---\n"
            yield full_response + page_header, full_response + page_header
            messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": text}]}]
            prompt_full = current_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = current_processor(text=[prompt_full], images=[image], return_tensors="pt", padding=True).to(device)
            streamer = TextIteratorStreamer(current_processor, skip_prompt=True, skip_special_tokens=True)
            generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens}
            thread = Thread(target=current_model.generate, kwargs=generation_kwargs)
            thread.start()
            page_buffer = ""
            for new_text in streamer:
                page_buffer += new_text
                yield full_response + page_header + page_buffer, full_response + page_header + page_buffer
                time.sleep(0.01)
            full_response += page_header + page_buffer + "\n\n"
    except Exception as e:
        logger.error(f"PDF生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


# @spaces.GPU
def generate_caption(image: Image.Image, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """图像描述生成函数，支持本地和在线模型"""
    if image is None:
        yield "Please upload an image to caption.", "Please upload an image to caption."
        return

    current_model_key = model_manager.current_model_key

    # 检查是否为在线模型
    if is_online_model(current_model_key):
        # 递归调用在线生成函数
        yield from _generate_caption_online(image, current_model_key, max_new_tokens, temperature, top_p, top_k, repetition_penalty)
    else:
        # 递归调用本地生成函数
        yield from _generate_caption_local(image, max_new_tokens, temperature, top_p, top_k, repetition_penalty)


def _generate_caption_local(image: Image.Image, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """本地模型图像描述生成"""
    current_model = model_manager.get_current_model()
    current_processor = model_manager.get_current_processor()

    if current_model is None or current_processor is None:
        yield "模型未加载", "模型未加载"
        return

    # 检查模型类型
    model_info = model_manager.get_current_model_info()
    if model_info.get("type") != "multimodal":
        yield "当前本地模型不支持图像描述，请切换到多模态模型", "当前本地模型不支持图像描述，请切换到多模态模型"
        return

    try:
        system_prompt = (
            "You are an AI assistant that rigorously follows this response protocol: For every input image, your primary "
            "task is to write a precise caption that captures the essence of the image in clear, concise, and contextually "
            "accurate language. Along with the caption, provide a structured set of attributes describing the visual "
            "elements, including details such as objects, people, actions, colors, environment, mood, and other notable "
            "characteristics. Ensure captions are precise, neutral, and descriptive, avoiding unnecessary elaboration or "
            "subjective interpretation unless explicitly required. Do not reference the rules or instructions in the output; "
            "only return the formatted caption, attributes, and class_name."
        )
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": system_prompt}]}]
        prompt_full = current_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = current_processor(text=[prompt_full], images=[image], return_tensors="pt", padding=True).to(device)
        streamer = TextIteratorStreamer(current_processor, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens}
        thread = Thread(target=current_model.generate, kwargs=generation_kwargs)
        thread.start()
        buffer = ""
        for new_text in streamer:
            buffer += new_text
            time.sleep(0.01)
            yield buffer, buffer
    except Exception as e:
        logger.error(f"本地图像描述生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


def _generate_caption_online(image: Image.Image, model_key: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """在线模型图像描述生成"""
    try:
        model_id = get_online_model_id(model_key)
        logger.info(f"使用在线模型生成图像描述: {model_id}")

        # 编码图像为base64
        image_base64 = encode_image_to_base64(image)

        # 系统提示词
        system_prompt = (
            "You are an AI assistant that rigorously follows this response protocol: For every input image, your primary "
            "task is to write a precise caption that captures the essence of the image in clear, concise, and contextually "
            "accurate language. Along with the caption, provide a structured set of attributes describing the visual "
            "elements, including details such as objects, people, actions, colors, environment, mood, and other notable "
            "characteristics. Ensure captions are precise, neutral, and descriptive, avoiding unnecessary elaboration or "
            "subjective interpretation unless explicitly required. Do not reference the rules or instructions in the output; "
            "only return the formatted caption, attributes, and class_name."
        )

        # 构建消息
        messages = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_base64}}, {"type": "text", "text": system_prompt}]}]

        # 构建生成参数
        params = {"model": model_id, "messages": messages, "max_tokens": max_new_tokens, "temperature": temperature, "top_p": top_p, "stream": True}

        # 使用流式生成
        buffer = ""
        for chunk in online_client.stream_generate_text(model_id, messages, **params):
            if chunk:
                buffer += chunk
                yield buffer, buffer

    except Exception as e:
        logger.error(f"在线图像描述生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"


# @spaces.GPU
def generate_gif(text: str, gif_path: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """GIF生成函数"""
    if gif_path is None:
        yield "Please upload a GIF.", "Please upload a GIF."
        return

    current_model = model_manager.get_current_model()
    current_processor = model_manager.get_current_processor()

    if current_model is None or current_processor is None:
        yield "模型未加载", "模型未加载"
        return

    # 检查模型类型
    model_info = model_manager.get_current_model_info()
    if model_info.get("type") != "multimodal":
        yield "当前模型不支持GIF处理，请切换到多模态模型", "当前模型不支持GIF处理，请切换到多模态模型"
        return

    try:
        frames = extract_gif_frames(gif_path)
        if not frames:
            yield "Could not process GIF.", "Could not process GIF."
            return
        messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        for _frame in frames:
            messages[0]["content"].insert(0, {"type": "image"})
        prompt_full = current_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = current_processor(text=[prompt_full], images=frames, return_tensors="pt", padding=True).to(device)
        streamer = TextIteratorStreamer(current_processor, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens, "do_sample": True, "temperature": temperature, "top_p": top_p, "top_k": top_k, "repetition_penalty": repetition_penalty}
        thread = Thread(target=current_model.generate, kwargs=generation_kwargs)
        thread.start()
        buffer = ""
        for new_text in streamer:
            buffer += new_text
            buffer = buffer.replace("<|im_end|>", "")
            time.sleep(0.01)
            yield buffer, buffer
    except Exception as e:
        logger.error(f"GIF生成失败: {e}")
        yield f"生成出错: {str(e)}", f"生成出错: {str(e)}"
