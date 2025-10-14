"""Media processing utilities for handling different file formats."""

from io import BytesIO
from typing import Any

import cv2
import fitz
import numpy as np
from PIL import Image


def extract_gif_frames(gif_path: str) -> list[Image.Image]:
    """Extract frames from a GIF file."""
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


def downsample_video(video_path: str) -> list[Image.Image]:
    """Extract and downsample frames from a video file."""
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


def convert_pdf_to_images(file_path: str, dpi: int = 200) -> list[Image.Image]:
    """Convert PDF pages to images."""
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


def get_initial_pdf_state() -> dict[str, Any]:
    """Get initial PDF state dictionary."""
    return {"pages": [], "total_pages": 0, "current_page_index": 0}


def load_and_preview_pdf(file_path: str | None) -> tuple[Image.Image | None, dict[str, Any], str]:
    """Load PDF and return preview of first page with navigation state."""
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
        return None, state, f'<div style="text-align:center;">Failed to load preview: {e}</div>'


def navigate_pdf_page(direction: str, state: dict[str, Any]) -> tuple[Image.Image | None, dict[str, Any], str]:
    """Navigate through PDF pages."""
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
