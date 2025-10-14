#!/usr/bin/env python3
"""
测试Web接口的文本生成功能
"""
import requests
import json

def test_web_interface():
    """测试Web接口的文本生成功能"""
    url = "http://localhost:13001"

    # 测试参数
    test_data = {
        "data": [
            "Hello, how are you?",  # text_query
            1024,  # max_new_tokens
            0.6,   # temperature
            0.9,   # top_p
            50,    # top_k
            1.2    # repetition_penalty
        ],
        "fn_index": 0  # This might be the index of the text generation function
    }

    try:
        print("Testing web interface text generation...")
        response = requests.post(f"{url}/api/predict", json=test_data)

        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error testing web interface: {e}")

if __name__ == "__main__":
    test_web_interface()