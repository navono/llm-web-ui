"""
Gradio主题和样式配置
"""

# 简化的CSS样式
css = """
#main-title h1 {
    font-size: 2.3em !important;
}
#output-title h2 {
    font-size: 2.1em !important;
}
.model-message { text-align: end; }
.model-dropdown-container { display: flex; align-items: center; gap: 10px; padding: 0; }
.user-input-container .multimodal-textbox{ border: none !important; }
.control-button { height: 51px; }
div.block.chatbot { height: calc(100svh - 320px) !important; max-height: 900px !important; }
div.no-padding { padding: 0 !important; }
@media (max-width: 1280px) { div.block.chatbot { height: calc(100svh - 320px) !important; } }
@media (max-width: 1024px) {
    .responsive-row { flex-direction: column; }
    .model-message { text-align: start; font-size: 10px !important; }
    .model-dropdown-container { flex-direction: column; align-items: flex-start; }
    div.block.chatbot { height: calc(100svh - 450px) !important; }
}
@media (max-width: 400px) {
    .responsive-row { flex-direction: column; }
    .model-message { text-align: start; font-size: 10px !important; }
    .model-dropdown-container { flex-direction: column; align-items: flex-start; }
    div.block.chatbot { max-height: 360px !important; }
}
@media (max-height: 932px) { .chatbot { max-height: 500px !important; } }
@media (max-height: 1280px) { div.block.chatbot { max-height: 800px !important; } }
"""


# 延迟加载主题，避免循环导入
def get_theme():
    import gradio as gr

    return gr.themes.Soft()


# 预设主题名称，稍后实例化
thistle_theme = None
