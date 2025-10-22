#!/usr/bin/env python3
"""
测试在线服务器连接和多模态功能
"""

import base64
import json
from io import BytesIO

import requests
from PIL import Image


def test_server_connection():
    """测试服务器连接"""
    print("🧪 测试在线服务器连接")
    print("=" * 50)

    try:
        # 测试连接
        print("1️⃣ 测试连接到localhost:8080...")
        base_url = "http://localhost:8080/v1"

        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 连接成功，状态码: {response.status_code}")

            if isinstance(data, dict) and 'data' in data:
                models = data['data']
                print(f"   📝 发现 {len(models)} 个模型:")
                for model in models:
                    print(f"      - {model.get('id', 'Unknown')}")
            else:
                print(f"   📝 响应格式: {type(data)}")

            return True
        else:
            print(f"   ❌ 连接失败，状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ 连接异常: {e}")
        return False

def test_multimodal_encoding():
    """测试多模态编码"""
    print("\n2️⃣ 测试图片base64编码...")

    # 创建测试图片
    test_image = Image.new('RGB', (100, 100), color='red')

    # 编码为base64
    buffered = BytesIO()
    test_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    base64_image = f"data:image/png;base64,{img_str}"

    print(f"   ✅ 图片编码成功，长度: {len(base64_image)} 字符")
    return base64_image

def test_online_vision_api():
    """测试在线视觉API"""
    print("\n3️⃣ 测试在线视觉API...")

    try:
        base_url = "http://localhost:8080/v1"

        # 获取模型列表
        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code != 200:
            print("   ❌ 无法获取模型列表")
            return False

        data = response.json()
        if isinstance(data, dict) and 'data' in data:
            models = data['data']
            if not models:
                print("   ❌ 没有可用的模型")
                return False

            # 使用第一个模型进行测试
            model_id = models[0]['id']
            print(f"   📝 使用模型: {model_id}")
        else:
            print("   ❌ 模型列表格式错误")
            return False

        # 创建测试图片
        test_image = Image.new('RGB', (100, 100), color='red')
        buffered = BytesIO()
        test_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        base64_image = f"data:image/png;base64,{img_str}"

        # 构建多模态消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "这个图片是什么颜色？"
                    }
                ]
            }
        ]

        # 测试流式生成
        print("   📤 发送请求...")
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": 50,
            "stream": True
        }

        response = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            stream=True,
            timeout=30
        )

        if response.status_code == 200:
            print("   ✅ 开始接收流式响应:")
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            line_str = line_str[6:]

                        if line_str == '[DONE]':
                            break

                        data = json.loads(line_str)
                        if 'choices' in data and data['choices']:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content = delta['content']
                                full_response += content
                                print(f"      {content}")
                    except json.JSONDecodeError:
                        continue

            print(f"   ✅ 完整响应: {full_response}")
            return True
        else:
            print(f"   ❌ API调用失败，状态码: {response.status_code}")
            print(f"   📝 错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ API调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始在线多模态功能测试")
    print("=" * 60)

    success = True

    # 测试服务器连接
    if not test_server_connection():
        success = False

    # 测试图片编码
    if success:
        test_multimodal_encoding()

    # 测试在线视觉API
    if success:
        if not test_online_vision_api():
            success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过!")
    else:
        print("❌ 部分测试失败")

    return success

if __name__ == "__main__":
    main()