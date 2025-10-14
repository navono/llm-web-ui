"""
Gradio UI组件
"""

import gradio as gr
from typing import Any
from .theme import get_theme, css
from .text_generation import generate_text, switch_model, connect_to_online_server as connect_to_server
from .multimodal_generation import (
    generate_image, generate_video, generate_pdf, generate_gif, generate_caption,
    load_and_preview_pdf, navigate_pdf_page, get_initial_pdf_state,
    MAX_MAX_NEW_TOKENS, DEFAULT_MAX_NEW_TOKENS
)
from ..model_manager import model_manager
from .online_client import is_online_model


def handle_connect_server(server_url: str):
    """处理连接服务器"""
    result = connect_to_server(server_url)

    if result["success"]:
        return (
            gr.Row(visible=True),  # online_models_row
            gr.Dropdown(choices=result["models"], value=None),  # online_model_dropdown
            gr.Button(visible=True),  # use_online_model_btn
        )
    else:
        return (
            gr.Row(visible=False),  # online_models_row
            gr.Dropdown(choices=[], value=None),  # online_model_dropdown
            gr.Button(visible=False),  # use_online_model_btn
        )


def handle_use_online_model(online_model_key: str):
    """处理使用在线模型"""
    if not online_model_key:
        return "请先选择在线模型", gr.Dropdown(), gr.Textbox()

    result = switch_model(online_model_key)

    # 更新当前模型显示
    current_model_status = f"当前模型: [Online] {online_model_key.split(':', 1)[1]}"

    # 更新主模型下拉框
    available_models = model_manager.get_available_models()
    model_choices = [(info["name"], key) for key, info in available_models.items()]

    # 添加在线模型到选择列表
    model_choices.append((online_model_key.split(":", 1)[1], online_model_key))

    return (
        gr.Dropdown(choices=model_choices, value=online_model_key),  # model_dropdown
        current_model_status  # current_model_display
    )


def update_model_status(model_key: str):
    """更新模型状态显示"""
    if is_online_model(model_key):
        return f"当前模型: [Online] {model_key.split(':', 1)[1]}"
    else:
        model_info = model_manager.get_current_model_info()
        return f"当前模型: [Local] {model_info.get('name', 'Unknown')}"


def create_interface():
    """创建完整的Gradio界面"""

    # 准备模型选择选项
    available_models = model_manager.get_available_models()
    model_choices = [(info["name"], key) for key, info in available_models.items()]
    current_model_key = model_manager.current_model_key

    with gr.Blocks(theme=get_theme(), css=css) as demo:
        pdf_state = gr.State(value=get_initial_pdf_state())
        gr.Markdown("# LLM Web UI", elem_id="main-title")

        # 模型选择区域
        with gr.Row():
            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=model_choices,
                    value=current_model_key,
                    label="本地模式 - 选择模型"
                )
                switch_model_btn = gr.Button("切换模型", variant="primary")

            with gr.Column(scale=1):
                with gr.Row():
                    server_url_input = gr.Textbox(
                        label="Online模式 - 服务器地址",
                        placeholder="http://localhost:18800/v1",
                        value="http://localhost:18800/v1"
                    )
                with gr.Row():
                    connect_server_btn = gr.Button("连接服务器", variant="primary")
                with gr.Row(visible=False) as online_models_row:
                    online_model_dropdown = gr.Dropdown(
                        choices=[],
                        label="选择在线模型",
                        info="从远程服务器选择模型"
                    )
                    use_online_model_btn = gr.Button("使用在线模型", variant="secondary")

        # 当前模型状态 - 始终显示在最下方
        current_model_display = gr.Textbox(
            value=update_model_status(current_model_key),
            label="当前模型",
            interactive=False,
            info="显示当前正在使用的AI模型"
        )

        # Tab选择行 - 独立一行显示
        with gr.Row():
            with gr.Tabs():
                with gr.TabItem("Text Generation"):
                    with gr.Column():
                        text_query = gr.Textbox(
                            label="Text Input",
                            placeholder="Enter your text prompt here...",
                            lines=3,
                            scale=3
                        )
                        text_submit = gr.Button("Submit", variant="primary", scale=1)

                with gr.TabItem("Image Inference"):
                    with gr.Column():
                        image_query = gr.Textbox(
                            label="Query Input",
                            placeholder="Enter your query here...",
                            scale=2
                        )
                        image_upload = gr.Image(type="pil", label="Image", height=290, scale=1)
                        image_submit = gr.Button("Submit", variant="primary", scale=1)

                with gr.TabItem("Video Inference"):
                    with gr.Column():
                        video_query = gr.Textbox(
                            label="Query Input",
                            placeholder="Enter your query here...",
                            scale=2
                        )
                        video_upload = gr.Video(label="Video", height=290, scale=1)
                        video_submit = gr.Button("Submit", variant="primary", scale=1)

                with gr.TabItem("PDF Inference"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            pdf_query = gr.Textbox(
                                label="Query Input",
                                placeholder="e.g., 'Summarize this document'"
                            )
                            pdf_upload = gr.File(label="Upload PDF", file_types=[".pdf"])
                            pdf_submit = gr.Button("Submit", variant="primary")
                        with gr.Column(scale=1):
                            pdf_preview_img = gr.Image(label="PDF Preview", height=290)
                            with gr.Row():
                                prev_page_btn = gr.Button("◀ Previous")
                                page_info = gr.HTML('<div style="text-align:center;">No file loaded</div>')
                                next_page_btn = gr.Button("Next ▶")

                with gr.TabItem("Gif Inference"):
                    with gr.Column():
                        gif_query = gr.Textbox(
                            label="Query Input",
                            placeholder="e.g., 'What is happening in this gif?'",
                            scale=2
                        )
                        gif_upload = gr.Image(type="filepath", label="Upload GIF", height=290, scale=1)
                        gif_submit = gr.Button("Submit", variant="primary", scale=1)

                with gr.TabItem("Caption"):
                    with gr.Column():
                        caption_image_upload = gr.Image(type="pil", label="Image to Caption", height=290, scale=1)
                        caption_submit = gr.Button("Submit", variant="primary", scale=1)

        # 高级选项 - 独立行显示
        with gr.Accordion("Advanced options", open=False):
            with gr.Row():
                max_new_tokens = gr.Slider(
                    label="Max new tokens",
                    minimum=1,
                    maximum=MAX_MAX_NEW_TOKENS,
                    step=1,
                    value=DEFAULT_MAX_NEW_TOKENS,
                    scale=1
                )
                temperature = gr.Slider(
                    label="Temperature",
                    minimum=0.1,
                    maximum=4.0,
                    step=0.1,
                    value=0.6,
                    scale=1
                )
                top_p = gr.Slider(
                    label="Top-p (nucleus sampling)",
                    minimum=0.05,
                    maximum=1.0,
                    step=0.05,
                    value=0.9,
                    scale=1
                )
                top_k = gr.Slider(
                    label="Top-k",
                    minimum=1,
                    maximum=1000,
                    step=1,
                    value=50,
                    scale=1
                )
                repetition_penalty = gr.Slider(
                    label="Repetition penalty",
                    minimum=1.0,
                    maximum=2.0,
                    step=0.05,
                    value=1.2,
                    scale=1
                )

        # 输出行 - 左右布局
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Output", elem_id="output-title")
                output = gr.Textbox(
                    label="Raw Output Stream",
                    interactive=False,
                    lines=14,
                    show_copy_button=True
                )
            with gr.Column(scale=1):
                with gr.Accordion("(Result.md)", open=False):
                    markdown_output = gr.Markdown(
                        label="(Result.Md)",
                        latex_delimiters=[
                            {"left": "$$", "right": "$$", "display": True},
                            {"left": "$", "right": "$", "display": False}
                        ]
                    )

        # 事件绑定
        # 文本生成事件绑定
        text_submit.click(
            fn=generate_text,
            inputs=[text_query, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )
        # 支持 Ctrl+Enter 快捷键
        text_query.submit(
            fn=generate_text,
            inputs=[text_query, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )

        # 模型切换事件绑定
        switch_model_btn.click(
            fn=switch_model,
            inputs=[model_dropdown],
            outputs=[current_model_display]
        )

        # Online模式事件绑定
        connect_server_btn.click(
            fn=handle_connect_server,
            inputs=[server_url_input],
            outputs=[online_models_row, online_model_dropdown, use_online_model_btn]
        )

        use_online_model_btn.click(
            fn=handle_use_online_model,
            inputs=[online_model_dropdown],
            outputs=[model_dropdown, current_model_display]
        )

        # 多模态事件绑定
        image_submit.click(
            fn=generate_image,
            inputs=[image_query, image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )
        # 支持 Ctrl+Enter 快捷键
        image_query.submit(
            fn=generate_image,
            inputs=[image_query, image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )

        video_submit.click(
            fn=generate_video,
            inputs=[video_query, video_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )
        # 支持 Ctrl+Enter 快捷键
        video_query.submit(
            fn=generate_video,
            inputs=[video_query, video_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )

        pdf_submit.click(
            fn=generate_pdf,
            inputs=[pdf_query, pdf_state, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )
        # 支持 Ctrl+Enter 快捷键
        pdf_query.submit(
            fn=generate_pdf,
            inputs=[pdf_query, pdf_state, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )

        gif_submit.click(
            fn=generate_gif,
            inputs=[gif_query, gif_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )
        # 支持 Ctrl+Enter 快捷键
        gif_query.submit(
            fn=generate_gif,
            inputs=[gif_query, gif_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )

        caption_submit.click(
            fn=generate_caption,
            inputs=[caption_image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty],
            outputs=[output, markdown_output]
        )

        # PDF相关事件绑定
        pdf_upload.change(
            fn=load_and_preview_pdf,
            inputs=[pdf_upload],
            outputs=[pdf_preview_img, pdf_state, page_info]
        )

        prev_page_btn.click(
            fn=lambda s: navigate_pdf_page("prev", s),
            inputs=[pdf_state],
            outputs=[pdf_preview_img, pdf_state, page_info]
        )

        next_page_btn.click(
            fn=lambda s: navigate_pdf_page("next", s),
            inputs=[pdf_state],
            outputs=[pdf_preview_img, pdf_state, page_info]
        )

    return demo