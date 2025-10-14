#!/usr/bin/env python3
"""
测试在线多模态功能
"""

import sys
sys.path.append('src')

def test_online_multimodal():
    """测试在线多模态功能"""
    print("🧪 测试在线多模态功能")
    print("=" * 50)

    try:
        # 测试导入
        print("1️⃣ 测试模块导入...")
        from src.gradio.online_client import connect_to_server
        from src.gradio.multimodal_generation import generate_image, encode_image_to_base64
        from PIL import Image
        import io
        import base64
        print("   ✅ 模块导入成功")

        # 连接到服务器
        print("\n2️⃣ 连接到localhost:18800...")
        result = connect_to_server("http://localhost:18800/v1")

        if not result["success"]:
            print(f"   ❌ 连接失败: {result['message']}")
            return False

        print(f"   ✅ {result['message']}")

        if not result['models']:
            print("   ⚠️ 没有可用的在线模型")
            return False

        # 查找VL模型
        vl_model = None
        for name, key in result['models']:
            if 'vl' in name.lower() or 'vision' in name.lower():
                vl_model = key
                break

        if not vl_model:
            print("   ⚠️ 没有找到VL模型，使用第一个可用模型")
            vl_model = result['models'][0][1]

        print(f"   📝 使用模型: {vl_model}")

        # 创建一个简单的测试图片
        print("\n3️⃣ 创建测试图片...")
        test_image = Image.new('RGB', (100, 100), color='red')
        print("   ✅ 测试图片创建成功")

        # 测试base64编码
        print("\n4️⃣ 测试图片base64编码...")
        encoded = encode_image_to_base64(test_image)
        print(f"   ✅ 图片编码成功，长度: {len(encoded)} 字符")

        # 测试在线图像生成
        print("\n5️⃣ 测试在线图像生成...")
        try:
            buffer = ""
            for chunk in generate_image("这个图片是什么颜色？", test_image, max_new_tokens=20):
                buffer = chunk
                print(f"   📤 生成中: {chunk[:50]}...")

            print(f"   ✅ 生成完成: {buffer[:100]}...")
            print("\n" + "=" * 50)
            print("🎉 在线多模态测试完成!")
            return True

        except Exception as e:
            print(f"   ❌ 在线生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_online_multimodal()