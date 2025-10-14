"""UI components and layout for the Gradio interface."""

import gradio as gr

from .examples import caption_examples, gif_examples, image_examples, pdf_examples, video_examples
from .generators import generate_caption, generate_gif, generate_image, generate_pdf, generate_video
from .media_processing import get_initial_pdf_state, load_and_preview_pdf, navigate_pdf_page
from .model import DEFAULT_MAX_NEW_TOKENS, MAX_MAX_NEW_TOKENS


def create_interface():
    """Create and return the main Gradio interface."""

    # Import theme and CSS
    from .theme import css, thistle_theme

    with gr.Blocks(theme=thistle_theme, css=css) as demo:
        pdf_state = gr.State(value=get_initial_pdf_state())

        # Main title
        gr.Markdown("# ** LLM Web UI **", elem_id="main-title")

        with gr.Row():
            with gr.Column(scale=2):
                with gr.Tabs():
                    # Image Inference Tab
                    with gr.TabItem("Image Inference"):
                        image_query = gr.Textbox(label="Query Input", placeholder="Enter your query here...")
                        image_upload = gr.Image(type="pil", label="Image", height=290)
                        image_submit = gr.Button("Submit", variant="primary")
                        gr.Examples(examples=image_examples, inputs=[image_query, image_upload])

                    # Video Inference Tab
                    with gr.TabItem("Video Inference"):
                        video_query = gr.Textbox(label="Query Input", placeholder="Enter your query here...")
                        video_upload = gr.Video(label="Video", height=290)
                        video_submit = gr.Button("Submit", variant="primary")
                        gr.Examples(examples=video_examples, inputs=[video_query, video_upload])

                    # PDF Inference Tab
                    with gr.TabItem("PDF Inference"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                pdf_query = gr.Textbox(label="Query Input", placeholder="e.g., 'Summarize this document'")
                                pdf_upload = gr.File(label="Upload PDF", file_types=[".pdf"])
                                pdf_submit = gr.Button("Submit", variant="primary")
                            with gr.Column(scale=1):
                                pdf_preview_img = gr.Image(label="PDF Preview", height=290)
                                with gr.Row():
                                    prev_page_btn = gr.Button("◀ Previous")
                                    page_info = gr.HTML('<div style="text-align:center;">No file loaded</div>')
                                    next_page_btn = gr.Button("Next ▶")
                        gr.Examples(examples=pdf_examples, inputs=[pdf_query, pdf_upload])

                    # GIF Inference Tab
                    with gr.TabItem("Gif Inference"):
                        gif_query = gr.Textbox(label="Query Input", placeholder="e.g., 'What is happening in this gif?'")
                        gif_upload = gr.Image(type="filepath", label="Upload GIF", height=290)
                        gif_submit = gr.Button("Submit", variant="primary")
                        gr.Examples(examples=gif_examples, inputs=[gif_query, gif_upload])

                    # Caption Tab
                    with gr.TabItem("Caption"):
                        caption_image_upload = gr.Image(type="pil", label="Image to Caption", height=290)
                        caption_submit = gr.Button("Generate Caption", variant="primary")
                        gr.Examples(examples=caption_examples, inputs=[caption_image_upload])

                # Advanced Options Accordion
                with gr.Accordion("Advanced options", open=False):
                    max_new_tokens = gr.Slider(label="Max new tokens", minimum=1, maximum=MAX_MAX_NEW_TOKENS, step=1, value=DEFAULT_MAX_NEW_TOKENS)
                    temperature = gr.Slider(label="Temperature", minimum=0.1, maximum=4.0, step=0.1, value=0.6)
                    top_p = gr.Slider(label="Top-p (nucleus sampling)", minimum=0.05, maximum=1.0, step=0.05, value=0.9)
                    top_k = gr.Slider(label="Top-k", minimum=1, maximum=1000, step=1, value=50)
                    repetition_penalty = gr.Slider(label="Repetition penalty", minimum=1.0, maximum=2.0, step=0.05, value=1.2)

            # Output Column
            with gr.Column(scale=3):
                gr.Markdown("## Output", elem_id="output-title")
                output = gr.Textbox(label="Raw Output Stream", interactive=False, lines=14, show_copy_button=True)
                with gr.Accordion("(Result.md)", open=False):
                    markdown_output = gr.Markdown(label="(Result.Md)", latex_delimiters=[{"left": "$$", "right": "$$", "display": True}, {"left": "$", "right": "$", "display": False}])

        # Event handlers
        _setup_event_handlers(
            image_query,
            image_upload,
            image_submit,
            video_query,
            video_upload,
            video_submit,
            pdf_query,
            pdf_upload,
            pdf_submit,
            pdf_preview_img,
            prev_page_btn,
            next_page_btn,
            page_info,
            gif_query,
            gif_upload,
            gif_submit,
            caption_image_upload,
            caption_submit,
            max_new_tokens,
            temperature,
            top_p,
            top_k,
            repetition_penalty,
            output,
            markdown_output,
            pdf_state,
        )

    return demo


def _setup_event_handlers(
    image_query,
    image_upload,
    image_submit,
    video_query,
    video_upload,
    video_submit,
    pdf_query,
    pdf_upload,
    pdf_submit,
    pdf_preview_img,
    prev_page_btn,
    next_page_btn,
    page_info,
    gif_query,
    gif_upload,
    gif_submit,
    caption_image_upload,
    caption_submit,
    max_new_tokens,
    temperature,
    top_p,
    top_k,
    repetition_penalty,
    output,
    markdown_output,
    pdf_state,
):
    """Setup all event handlers for the interface."""

    # Generation function handlers
    image_submit.click(fn=generate_image, inputs=[image_query, image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

    video_submit.click(fn=generate_video, inputs=[video_query, video_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

    pdf_submit.click(fn=generate_pdf, inputs=[pdf_query, pdf_state, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

    gif_submit.click(fn=generate_gif, inputs=[gif_query, gif_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

    caption_submit.click(fn=generate_caption, inputs=[caption_image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

    # PDF navigation handlers
    pdf_upload.change(fn=load_and_preview_pdf, inputs=[pdf_upload], outputs=[pdf_preview_img, pdf_state, page_info])

    prev_page_btn.click(fn=lambda s: navigate_pdf_page("prev", s), inputs=[pdf_state], outputs=[pdf_preview_img, pdf_state, page_info])

    next_page_btn.click(fn=lambda s: navigate_pdf_page("next", s), inputs=[pdf_state], outputs=[pdf_preview_img, pdf_state, page_info])
