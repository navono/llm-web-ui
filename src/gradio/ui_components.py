"""
Gradio UI组件
"""

import gradio as gr

from .jina_tools import generate_embeddings, read_url, rerank_documents, search_web
from .multimodal_generation import DEFAULT_MAX_NEW_TOKENS, MAX_MAX_NEW_TOKENS, generate_caption, generate_gif, generate_image, generate_pdf, generate_video, get_initial_pdf_state, load_and_preview_pdf, navigate_pdf_page
from .online_client import is_online_model
from .speech import generate_speech_to_text, generate_text_to_speech, get_available_voices
from .text_generation import connect_to_online_server as connect_to_server
from .text_generation import generate_text, switch_model
from .theme import css, get_theme

default_online_url = "http://localhost:8080/v1"


def handle_set_api_key(api_key: str):
    """处理设置 API Key"""
    from loguru import logger

    from .online_client import online_client

    if api_key and api_key.strip():
        online_client.set_api_key(api_key.strip())
        logger.info("API Key 已更新")
        gr.Info("✅ API Key 已设置")
        return '<div style="padding:6px 10px;border-radius:6px;background:#e8f5e9;color:#1b5e20;">🔑 API Key 已设置</div>'
    else:
        online_client.set_api_key("")
        logger.info("API Key 已清除")
        gr.Info("API Key 已清除")
        return '<div style="padding:6px 10px;border-radius:6px;background:#fff3e0;color:#e65100;">⚠️ API Key 已清除</div>'


def handle_connect_server(server_url: str):
    """处理连接服务器"""
    from loguru import logger

    # 强制打印，确保函数被调用
    print(f"\n{'=' * 50}\n[CONNECT] handle_connect_server called with URL: {server_url}\n{'=' * 50}\n", flush=True)
    logger.debug(f"[UI] 连接服务器：{server_url}")
    try:
        result = connect_to_server(server_url)
        logger.info(f"[UI] handle_connect_server called, url={server_url}, success={result.get('success')}, error={result.get('error')}")
        logger.debug(f"[UI] 连接服务器结果: {result}")
    except Exception as exc:  # 捕获并显示异常，避免静默失败
        logger.exception(f"[UI] 连接服务器异常: {exc}")
        gr.Error(f"连接服务器异常: {exc}")
        return (gr.Row(visible=False), gr.Dropdown(choices=[], value=None), gr.Button(visible=False), "<div style='color:#b71c1c;'>连接异常</div>")

    if result["success"]:
        logger.info("连接成功，显示成功提示")
        gr.Info(f"成功连接到服务器: {server_url}")
        return (
            gr.Row(visible=True),  # online_models_row
            gr.Dropdown(choices=result["models"], value=None),  # online_model_dropdown
            gr.Button(visible=True),  # use_online_model_btn
            f'<div style="padding:6px 10px;border-radius:6px;background:#e8f5e9;color:#1b5e20;">✅ 已连接到服务器：<b>{server_url}</b></div>',
        )
    else:
        error_msg = result.get("error", "连接失败")
        logger.error(f"连接失败，显示错误提示: {error_msg}")
        gr.Error(f"连接服务器失败: {error_msg}")
        return (
            gr.Row(visible=False),  # online_models_row
            gr.Dropdown(choices=[], value=None),  # online_model_dropdown
            gr.Button(visible=False),  # use_online_model_btn
            f'<div style="padding:6px 10px;border-resize:6px;background:#ffebee;color:#b71c1c;">❌ 连接服务器失败：{error_msg}</div>',
        )


def handle_use_online_model(online_model_key: str):
    """处理使用在线模型"""
    from loguru import logger

    logger.info(f"handle_use_online_model 被调用，模型: {online_model_key}")

    if not online_model_key:
        gr.Warning("请先选择在线模型")
        return gr.Textbox(), gr.Dropdown()

    switch_model(online_model_key)
    gr.Info(f"已切换到在线模型: {online_model_key.split(':', 1)[1]}")

    # 更新当前模型显示
    current_model_status = f"当前模型: [Online] {online_model_key.split(':', 1)[1]}"

    # 如果选择的是 indextts2 模型，自动更新语音列表
    voices_dropdown = gr.Dropdown()
    model_name = online_model_key.split(":", 1)[1].lower()
    logger.info(f"检查模型名称: {model_name}")
    if "indextts2" in model_name or "tts" in model_name:
        logger.info("检测到 TTS 模型，开始获取语音列表...")
        # 自动请求语音列表
        voices_result = get_available_voices()
        logger.info(f"语音列表结果: {voices_result}")
        if voices_result.get("success"):
            voices = voices_result.get("voices", [])
            if voices:
                voices_dropdown = gr.Dropdown(choices=voices, value=voices[0])
                gr.Info(f"已加载 {len(voices)} 个语音选项")
                logger.info(f"成功更新语音下拉框，共 {len(voices)} 个选项")
            else:
                voices_dropdown = gr.Dropdown(choices=[], value="")
                logger.warning("语音列表为空")
        else:
            voices_dropdown = gr.Dropdown(choices=[], value="")
            logger.error(f"获取语音列表失败: {voices_result.get('error')}")
    else:
        logger.info("非 TTS 模型，跳过语音列表加载")

    return current_model_status, voices_dropdown


def update_model_status(model_key: str):
    """更新模型状态显示"""
    if is_online_model(model_key):
        return f"当前模型: [Online] {model_key.split(':', 1)[1]}"
    else:
        return "当前模型: 未连接在线模型"


def update_tts_voices():
    """更新 TTS 声音列表"""
    result = get_available_voices()
    if result.get("success"):
        voices = result.get("voices", [])
        return gr.Dropdown(choices=voices, value=voices[0] if voices else "alloy")
    else:
        # 返回默认声音列表
        default_voices = []
        return gr.Dropdown(choices=default_voices, value="alloy")


def create_interface():
    """创建完整的Gradio界面"""

    with gr.Blocks(theme=get_theme(), css=css) as demo:
        pdf_state = gr.State(value=get_initial_pdf_state())
        gr.Markdown("# LLM Web UI", elem_id="main-title")

        # 模型选择区域
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    server_url_input = gr.Textbox(label="服务器地址", placeholder=default_online_url, value=default_online_url)
                with gr.Row():
                    connect_server_btn = gr.Button("连接服务器", variant="primary")
                # 在线模式状态提示区域（确保无论通知是否可用，都有可见反馈）
                connect_status = gr.HTML(value="", elem_id="online-connect-status")
                with gr.Row(visible=False) as online_models_row:
                    online_model_dropdown = gr.Dropdown(choices=[], label="选择在线模型", info="从远程服务器选择模型")
                    use_online_model_btn = gr.Button("使用在线模型", variant="secondary")

            with gr.Column(scale=1):
                with gr.Row():
                    api_key_input = gr.Textbox(label="API Key", placeholder="sk-your-api-key-here", type="password", info="用于所有 API 请求的认证密钥")
                    set_api_key_btn = gr.Button("设置 API Key", variant="secondary", scale=0)
                # API Key 状态提示
                api_key_status = gr.HTML(value="", elem_id="api-key-status")

        # 当前模型状态 - 始终显示在最下方
        current_model_display = gr.Textbox(value="当前模型: 未连接在线模型", label="当前模型", interactive=False, info="显示当前正在使用的AI模型")

        # Tab选择行 - 独立一行显示
        with gr.Tabs():
            with gr.TabItem("Text Generation"), gr.Column():
                text_query = gr.Textbox(label="Text Input", placeholder="Enter your text prompt here...", lines=3, scale=3)
                with gr.Accordion("Advanced options", open=False), gr.Row():
                    max_new_tokens = gr.Slider(label="Max new tokens", minimum=1, maximum=MAX_MAX_NEW_TOKENS, step=1, value=DEFAULT_MAX_NEW_TOKENS, scale=1)
                    temperature = gr.Slider(label="Temperature", minimum=0.1, maximum=4.0, step=0.1, value=0.6, scale=1)
                    top_p = gr.Slider(label="Top-p (nucleus sampling)", minimum=0.05, maximum=1.0, step=0.05, value=0.9, scale=1)
                    top_k = gr.Slider(label="Top-k", minimum=1, maximum=1000, step=1, value=50, scale=1)
                    repetition_penalty = gr.Slider(label="Repetition penalty", minimum=1.0, maximum=2.0, step=0.05, value=1.2, scale=1)
                text_submit = gr.Button("Submit", variant="primary", scale=1)

            with gr.TabItem("Image Inference"), gr.Column():
                image_query = gr.Textbox(label="Query Input", placeholder="Enter your query here...", scale=2)
                image_upload = gr.Image(type="pil", label="Image", height=290, scale=1)
                image_submit = gr.Button("Submit", variant="primary", scale=1)

            with gr.TabItem("Video Inference"), gr.Column():
                video_query = gr.Textbox(label="Query Input", placeholder="Enter your query here...", scale=2)
                video_upload = gr.Video(label="Video", height=290, scale=1)
                video_submit = gr.Button("Submit", variant="primary", scale=1)

            with gr.TabItem("PDF Inference"), gr.Row():
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

            with gr.TabItem("Gif Inference"), gr.Column():
                gif_query = gr.Textbox(label="Query Input", placeholder="e.g., 'What is happening in this gif?'", scale=2)
                gif_upload = gr.Image(type="filepath", label="Upload GIF", height=290, scale=1)
                gif_submit = gr.Button("Submit", variant="primary", scale=1)

            with gr.TabItem("Caption"), gr.Column():
                caption_image_upload = gr.Image(type="pil", label="Image to Caption", height=290, scale=1)
                caption_submit = gr.Button("Submit", variant="primary", scale=1)

            with gr.TabItem("Speech2Text"), gr.Column():
                audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Upload Audio or Record")
                speech_submit = gr.Button("Submit", variant="primary", scale=1)

            with gr.TabItem("Text2Speech"), gr.Column():
                tts_text_input = gr.Textbox(label="Text Input", placeholder="Enter text to convert to speech...", lines=5, scale=1)
                with gr.Row():
                    tts_voice = gr.Dropdown(choices=[], value="", label="Voice", scale=1)
                    tts_speed = gr.Slider(label="Speed", minimum=0.25, maximum=4.0, step=0.25, value=1.0, scale=1)
                tts_submit = gr.Button("Generate Speech", variant="primary", scale=1)
                tts_audio_output = gr.Audio(label="Generated Audio", type="filepath", show_download_button=True, scale=1)

            with gr.TabItem("Embeddings"), gr.Column():
                gr.Markdown("### 文本向量化\n将文本转换为向量表示，每行一个文本")
                embeddings_text_input = gr.Textbox(label="文本输入", placeholder="输入文本，每行一个\n例如：\nHello world\n你好世界\nBonjour le monde", lines=8, scale=1)
                embeddings_model = gr.Dropdown(choices=["jina-embeddings-v3", "jina-embeddings-v4"], value="jina-embeddings-v3", label="模型", scale=1)
                with gr.Accordion("Advanced options", open=False):
                    embeddings_task = gr.Dropdown(choices=["text-matching", "retrieval.query", "retrieval.passage", "separation", "classification", "none"], value="text-matching", label="下游任务 (task)", info="针对不同任务优化向量")
                    embeddings_encoding = gr.Dropdown(
                        choices=[("默认 (浮点型)", "float"), ("二进制 (int8)", "int8"), ("二进制 (uint8)", "uint8"), ("Base64 (字符串)", "base64")],
                        value="float",
                        label="输出数据类型 (encoding_format)",
                        info="float: 浮点数 | int8/uint8: 整数 | base64: 字符串",
                    )
                embeddings_submit = gr.Button("生成 Embeddings", variant="primary", scale=1)

            with gr.TabItem("Rerank"), gr.Column():
                gr.Markdown("### 文档重排序\n根据查询相关性对文档进行排序")
                rerank_query = gr.Textbox(label="查询文本", placeholder="例如：Python programming tutorial", lines=2, scale=1)
                rerank_docs_input = gr.Textbox(label="文档列表", placeholder="输入文档，每行一个\n例如：\nLearn Python basics in 30 days\nJavaScript for beginners\nAdvanced Python programming guide", lines=8, scale=1)
                rerank_model = gr.Dropdown(choices=["jina-reranker-v2-base-multilingual", "jina-reranker-m0", "jina-reranker-v3"], value="jina-reranker-v2-base-multilingual", label="模型", scale=1)
                with gr.Accordion("Advanced options", open=False):
                    rerank_top_n = gr.Slider(label="返回数量", minimum=1, maximum=20, step=1, value=3)
                rerank_submit = gr.Button("重排序", variant="primary", scale=1)

            with gr.TabItem("Search"), gr.Column():
                gr.Markdown("### 网页搜索\n搜索互联网内容或抓取特定网页")
                search_query = gr.Textbox(label="搜索查询", placeholder="例如：Python programming tutorial", lines=1, scale=1)
                search_url = gr.Textbox(label="或输入 URL", placeholder="例如：https://example.com", lines=1, scale=1)
                with gr.Accordion("Advanced options", open=False):
                    search_respond_with = gr.Dropdown(
                        choices=["default", "no-content", "markdown", "html", "text", "screenshot"], value="default", label="响应格式 (X-Respond-With)", info="default: 完整内容 | no-content: 仅元数据 | markdown: Markdown 格式"
                    )
                    with gr.Row():
                        search_with_images = gr.Checkbox(label="包含图片摘要 (X-With-Images-Summary)", value=False)
                        search_with_links = gr.Checkbox(label="包含链接摘要 (X-With-Links-Summary)", value=False)
                search_submit = gr.Button("搜索", variant="primary", scale=1)

            with gr.TabItem("Reader"), gr.Column():
                gr.Markdown("### 网页内容提取\n将网页转换为 LLM 友好的干净文本")
                reader_url = gr.Textbox(label="URL", placeholder="例如：https://news.ycombinator.com", lines=1, scale=1)
                with gr.Accordion("Advanced options", open=False):
                    reader_engine = gr.Dropdown(choices=["direct", "browser"], value="direct", label="引擎 (X-Engine)", info="direct: 快速直接抓取 | browser: 使用浏览器渲染")
                    with gr.Row():
                        reader_with_images = gr.Checkbox(label="包含图片摘要 (X-With-Images-Summary)", value=False)
                        reader_with_links = gr.Checkbox(label="包含链接摘要 (X-With-Links-Summary)", value=False)
                reader_submit = gr.Button("读取", variant="primary", scale=1)

        # 输出行 - 左右布局
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Output", elem_id="output-title")
                output = gr.Textbox(label="Raw Output Stream", interactive=False, lines=14, show_copy_button=True)
            with gr.Column(scale=1), gr.Accordion("(Result.md)", open=False):
                markdown_output = gr.Markdown(label="(Result.Md)", latex_delimiters=[{"left": "$$", "right": "$$", "display": True}, {"left": "$", "right": "$", "display": False}])

        # 事件绑定
        # 文本生成事件绑定
        text_submit.click(fn=generate_text, inputs=[text_query, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])
        # 支持 Ctrl+Enter 快捷键
        text_query.submit(fn=generate_text, inputs=[text_query, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

        # 模型切换事件绑定
        # switch_model_btn.click(fn=switch_model, inputs=[model_dropdown], outputs=[current_model_display])

        # Online模式事件绑定
        # API Key 设置
        set_api_key_btn.click(
            fn=handle_set_api_key,
            inputs=[api_key_input],
            outputs=[api_key_status],
        )

        # 连接服务器
        connect_server_btn.click(
            fn=handle_connect_server,
            inputs=[server_url_input],
            outputs=[online_models_row, online_model_dropdown, use_online_model_btn, connect_status],
        )

        use_online_model_btn.click(fn=handle_use_online_model, inputs=[online_model_dropdown], outputs=[current_model_display, tts_voice])

        # 多模态事件绑定
        image_submit.click(fn=generate_image, inputs=[image_query, image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])
        # 支持 Ctrl+Enter 快捷键
        image_query.submit(fn=generate_image, inputs=[image_query, image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

        video_submit.click(fn=generate_video, inputs=[video_query, video_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])
        # 支持 Ctrl+Enter 快捷键
        video_query.submit(fn=generate_video, inputs=[video_query, video_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

        pdf_submit.click(fn=generate_pdf, inputs=[pdf_query, pdf_state, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])
        # 支持 Ctrl+Enter 快捷键
        pdf_query.submit(fn=generate_pdf, inputs=[pdf_query, pdf_state, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

        gif_submit.click(fn=generate_gif, inputs=[gif_query, gif_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])
        # 支持 Ctrl+Enter 快捷键
        gif_query.submit(fn=generate_gif, inputs=[gif_query, gif_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

        caption_submit.click(fn=generate_caption, inputs=[caption_image_upload, max_new_tokens, temperature, top_p, top_k, repetition_penalty], outputs=[output, markdown_output])

        speech_submit.click(fn=generate_speech_to_text, inputs=[audio_input], outputs=[output, markdown_output])

        tts_submit.click(fn=generate_text_to_speech, inputs=[tts_text_input, tts_voice, tts_speed], outputs=[tts_audio_output, markdown_output])

        # Embeddings 事件绑定
        embeddings_submit.click(fn=generate_embeddings, inputs=[embeddings_text_input, embeddings_model, embeddings_task, embeddings_encoding], outputs=[output, markdown_output])

        # Rerank 事件绑定
        rerank_submit.click(fn=rerank_documents, inputs=[rerank_query, rerank_docs_input, rerank_model, rerank_top_n], outputs=[output, markdown_output])

        # Search 事件绑定
        search_submit.click(fn=search_web, inputs=[search_query, search_url, search_respond_with, search_with_images, search_with_links], outputs=[output, markdown_output])

        # Reader 事件绑定
        reader_submit.click(fn=read_url, inputs=[reader_url, reader_engine, reader_with_images, reader_with_links], outputs=[output, markdown_output])

        # PDF相关事件绑定
        pdf_upload.change(fn=load_and_preview_pdf, inputs=[pdf_upload], outputs=[pdf_preview_img, pdf_state, page_info])

        prev_page_btn.click(fn=lambda s: navigate_pdf_page("prev", s), inputs=[pdf_state], outputs=[pdf_preview_img, pdf_state, page_info])

        next_page_btn.click(fn=lambda s: navigate_pdf_page("next", s), inputs=[pdf_state], outputs=[pdf_preview_img, pdf_state, page_info])

    return demo
