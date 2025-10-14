#!/usr/bin/env python3
"""
完整测试在线多模态功能的集成
"""

import base64
import json
from io import BytesIO

import requests
from PIL import Image


def test_online_multimodal_complete():
    """完整测试在线多模态功能"""
    print("🚀 完整测试在线多模态功能")
    print("=" * 60)

    try:
        # 步骤1: 连接到服务器
        print("1️⃣ 连接到localhost:18800...")
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

        # 步骤2: 创建测试图片
        print("\n2️⃣ 创建测试图片...")
        test_image = Image.new('RGB', (200, 200), color='blue')

        # 添加一些简单的图案
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([50, 50, 150, 150], fill='red')
        draw.ellipse([75, 75, 125, 125], fill='yellow')

        print("   ✅ 测试图片创建成功")

        # 步骤3: 编码图片
        print("\n3️⃣ 编码图片为base64...")
        buffered = BytesIO()
        test_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        base64_image = f"data:image/png;base64,{img_str}"
        print(f"   ✅ 图片编码成功，长度: {len(base64_image)} 字符")

        # 步骤4: 发送多模态请求
        print("\n4️⃣ 发送多模态请求...")

        test_queries = [
            "这张图片有什么内容？",
            "图片中的主要颜色是什么？",
            "描述一下图片中的几何形状"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n   4.{i} 测试查询: {query}")

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
                            "text": query
                        }
                    ]
                }
            ]

            payload = {
                "model": model_id,
                "messages": messages,
                "max_tokens": 100,
                "temperature": 0.7,
                "stream": True
            }

            try:
                response = requests.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    stream=True,
                    timeout=30
                )

                if response.status_code == 200:
                    print("      📤 响应:")
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
                                        print(f"         {content}", end="", flush=True)
                            except json.JSONDecodeError:
                                continue
                    print(f"\n      ✅ 完整响应: {full_response}")
                else:
                    print(f"      ❌ 请求失败，状态码: {response.status_code}")
                    print(f"      📝 错误信息: {response.text}")

            except Exception as e:
                print(f"      ❌ 请求异常: {e}")

        # 步骤5: 测试不同参数
        print("\n5️⃣ 测试不同参数设置...")

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
                        "text": "详细描述这张图片"
                    }
                ]
            }
        ]

        # 测试低温度
        payload_low_temp = {
            "model": model_id,
            "messages": messages,
            "max_tokens": 50,
            "temperature": 0.1,
            "stream": False
        }

        response = requests.post(
            f"{base_url}/chat/completions",
            json=payload_low_temp,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                print(f"   📤 低温度响应: {content}")
            else:
                print("   ❌ 响应格式错误")
        else:
            print(f"   ❌ 低温度测试失败，状态码: {response.status_code}")

        print("\n" + "=" * 60)
        print("🎉 在线多模态功能测试完成!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_online_multimodal_complete()