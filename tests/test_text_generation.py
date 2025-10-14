#!/usr/bin/env python3
"""
测试文本生成功能
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.gradio.text_generation import generate_text
from src.model_manager import model_manager


def test_text_generation():
    """测试文本生成功能"""
    print("Testing text generation with local model...")

    # 首先加载模型
    print("Loading model...")
    success = model_manager.load_model()
    if not success:
        print("Failed to load model!")
        return

    print(f"Current model: {model_manager.current_model_key}")
    print(f"Model loaded: {model_manager.get_current_model() is not None}")

    # 测试参数
    test_prompt = "Hello, how are you?"
    max_new_tokens = 50
    temperature = 0.6
    top_p = 0.9
    top_k = 50
    repetition_penalty = 1.2

    try:
        # 调用生成函数
        print("Testing text generation...")
        for output, markdown_output in generate_text(
            test_prompt, max_new_tokens, temperature, top_p, top_k, repetition_penalty
        ):
            print(f"Output: {output}")
            print(f"Markdown: {markdown_output}")
            print("-" * 50)

    except Exception as e:
        print(f"Error during text generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_generation()