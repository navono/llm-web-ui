"""Generation functions for different media types."""

import time
from threading import Thread
from typing import Any

import spaces
from PIL import Image
from transformers import TextIteratorStreamer

from .media_processing import downsample_video, extract_gif_frames
from .model import device, model_q3vl, processor_q3vl


@spaces.GPU
def generate_image(text: str, image: Image.Image, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """Generate text response for an image input."""
    if image is None:
        yield "Please upload an image.", "Please upload an image."
        return
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": text}]}]
    prompt_full = processor_q3vl.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor_q3vl(text=[prompt_full], images=[image], return_tensors="pt", padding=True).to(device)
    streamer = TextIteratorStreamer(processor_q3vl, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens}
    thread = Thread(target=model_q3vl.generate, kwargs=generation_kwargs)
    thread.start()
    buffer = ""
    for new_text in streamer:
        buffer += new_text
        time.sleep(0.01)
        yield buffer, buffer


@spaces.GPU
def generate_video(text: str, video_path: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """Generate text response for a video input."""
    if video_path is None:
        yield "Please upload a video.", "Please upload a video."
        return
    frames = downsample_video(video_path)
    if not frames:
        yield "Could not process video.", "Could not process video."
        return
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
    for frame in frames:
        messages[0]["content"].insert(0, {"type": "image"})
    prompt_full = processor_q3vl.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor_q3vl(text=[prompt_full], images=frames, return_tensors="pt", padding=True).to(device)
    streamer = TextIteratorStreamer(processor_q3vl, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens, "do_sample": True, "temperature": temperature, "top_p": top_p, "top_k": top_k, "repetition_penalty": repetition_penalty}
    thread = Thread(target=model_q3vl.generate, kwargs=generation_kwargs)
    thread.start()
    buffer = ""
    for new_text in streamer:
        buffer += new_text
        buffer = buffer.replace("<|im_end|>", "")
        time.sleep(0.01)
        yield buffer, buffer


@spaces.GPU
def generate_pdf(text: str, state: dict[str, Any], max_new_tokens: int = 2048, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """Generate text response for a PDF input."""
    if not state or not state["pages"]:
        yield "Please upload a PDF file first.", "Please upload a PDF file first."
        return
    page_images = state["pages"]
    full_response = ""
    for i, image in enumerate(page_images):
        page_header = f"--- Page {i + 1}/{len(page_images)} ---\n"
        yield full_response + page_header, full_response + page_header
        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": text}]}]
        prompt_full = processor_q3vl.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor_q3vl(text=[prompt_full], images=[image], return_tensors="pt", padding=True).to(device)
        streamer = TextIteratorStreamer(processor_q3vl, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens}
        thread = Thread(target=model_q3vl.generate, kwargs=generation_kwargs)
        thread.start()
        page_buffer = ""
        for new_text in streamer:
            page_buffer += new_text
            yield full_response + page_header + page_buffer, full_response + page_header + page_buffer
            time.sleep(0.01)
        full_response += page_header + page_buffer + "\n\n"


@spaces.GPU
def generate_caption(image: Image.Image, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """Generate caption for an image."""
    if image is None:
        yield "Please upload an image to caption.", "Please upload an image to caption."
        return
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
    prompt_full = processor_q3vl.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor_q3vl(text=[prompt_full], images=[image], return_tensors="pt", padding=True).to(device)
    streamer = TextIteratorStreamer(processor_q3vl, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens}
    thread = Thread(target=model_q3vl.generate, kwargs=generation_kwargs)
    thread.start()
    buffer = ""
    for new_text in streamer:
        buffer += new_text
        time.sleep(0.01)
        yield buffer, buffer


@spaces.GPU
def generate_gif(text: str, gif_path: str, max_new_tokens: int = 1024, temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2):
    """Generate text response for a GIF input."""
    if gif_path is None:
        yield "Please upload a GIF.", "Please upload a GIF."
        return
    frames = extract_gif_frames(gif_path)
    if not frames:
        yield "Could not process GIF.", "Could not process GIF."
        return
    messages = [{"role": "user", "content": [{"type": "text", "text": text}]}]
    for frame in frames:
        messages[0]["content"].insert(0, {"type": "image"})
    prompt_full = processor_q3vl.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor_q3vl(text=[prompt_full], images=frames, return_tensors="pt", padding=True).to(device)
    streamer = TextIteratorStreamer(processor_q3vl, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = {**inputs, "streamer": streamer, "max_new_tokens": max_new_tokens, "do_sample": True, "temperature": temperature, "top_p": top_p, "top_k": top_k, "repetition_penalty": repetition_penalty}
    thread = Thread(target=model_q3vl.generate, kwargs=generation_kwargs)
    thread.start()
    buffer = ""
    for new_text in streamer:
        buffer += new_text
        buffer = buffer.replace("<|im_end|>", "")
        time.sleep(0.01)
        yield buffer, buffer
