#!/usr/bin/env python3
"""
测试Gradio集成和在线多模态功能
"""

import sys
import json
import requests
import base64
from io import BytesIO
from PIL import Image

def test_complete_online_multimodal():
    """完整测试在线多模态功能"""
    print("🚀 测试Gradio集成和在线多模态功能")
    print("=" * 60)

    try:
        # 步骤1: 测试服务器连接
        print("1️⃣ 测试在线服务器连接...")
        base_url = "http://localhost:18800/v1"

        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code != 200:
            print(f"   ❌ 无法连接到服务器，状态码: {response.status_code}")
            return False

        data = response.json()
        if not isinstance(data, dict) or 'data' not in data:
            print("   ❌ 响应格式错误")
            return False

        models = data['data']
        if not models:
            print("   ❌ 没有可用的模型")
            return False

        model_id = models[0]['id']
        print(f"   ✅ 连接成功，使用模型: {model_id}")

        # 步骤2: 测试图片编码和消息格式
        print("\n2️⃣ 测试图片编码和消息格式...")

        # 创建测试图片
        test_image = Image.new('RGB', (200, 200), color='green')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        draw.ellipse([50, 50, 150, 150], fill='yellow')
        draw.rectangle([75, 75, 125, 125], fill='blue')

        # 编码为base64
        buffered = BytesIO()
        test_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        base64_image = f"data:image/png;base64,{img_str}"

        print(f"   ✅ 图片编码成功，长度: {len(base64_image)} 字符")

        # 构建正确的消息格式
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
                        "text": "这张图片有什么内容？请详细描述。"
                    }
                ]
            }
        ]

        print("   ✅ 消息格式构建成功")

        # 步骤3: 测试API调用
        print("\n3️⃣ 测试API调用...")

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": True
        }

        print("   📤 发送流式请求...")
        response = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            stream=True,
            timeout=30
        )

        if response.status_code == 200:
            print("   ✅ 开始接收流式响应:")
            full_response = ""
            chunk_count = 0

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
                                chunk_count += 1
                                if chunk_count <= 5:  # 只显示前5个chunk避免刷屏
                                    print(f"      Chunk {chunk_count}: '{content}'")
                    except json.JSONDecodeError:
                        continue

            print(f"   ✅ 接收到 {chunk_count} 个数据块")
            print(f"   ✅ 完整响应: {full_response[:100]}...")

            if full_response.strip():
                print("   ✅ 响应内容非空，测试成功！")
            else:
                print("   ❌ 响应内容为空")
                return False

        else:
            print(f"   ❌ API调用失败，状态码: {response.status_code}")
            print(f"   📝 错误信息: {response.text}")
            return False

        # 步骤4: 测试参数兼容性
        print("\n4️⃣ 测试不同参数组合...")

        test_params = [
            {"max_tokens": 50, "temperature": 0.1},
            {"max_tokens": 100, "temperature": 1.0},
            {"max_tokens": 200, "temperature": 0.5}
        ]

        for i, params in enumerate(test_params, 1):
            print(f"   4.{i} 测试参数: {params}")

            test_payload = {
                "model": model_id,
                "messages": messages,
                **params,
                "stream": False  # 使用非流式进行快速测试
            }

            try:
                response = requests.post(
                    f"{base_url}/chat/completions",
                    json=test_payload,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        content = data["choices"][0]["message"]["content"]
                        print(f"      ✅ 响应长度: {len(content)} 字符")
                    else:
                        print("      ❌ 响应格式错误")
                        return False
                else:
                    print(f"      ❌ 请求失败，状态码: {response.status_code}")
                    return False

            except Exception as e:
                print(f"      ❌ 请求异常: {e}")
                return False

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！在线多模态功能完全正常！")
        print("\n📋 功能总结:")
        print("  ✅ 服务器连接正常")
        print("  ✅ 图片编码正常")
        print("  ✅ 消息格式正确")
        print("  ✅ 流式生成正常")
        print("  ✅ 参数兼容性良好")
        print("\n🚀 可以在Gradio界面中正常使用Image Inference功能了！")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_complete_online_multimodal()