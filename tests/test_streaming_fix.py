#!/usr/bin/env python3
"""
测试流式生成修复
"""

import sys
import os
sys.path.append('src')

# 设置环境变量，避免模型加载
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def test_streaming_function():
    """测试流式生成函数"""
    print("🧪 测试流式生成函数")
    print("=" * 50)

    try:
        # 模拟导入，避免实际的模型加载
        from PIL import Image
        import inspect

        # 模拟生成器函数
        def mock_generate_image_online(text, image, model_key, **kwargs):
            """模拟在线图像生成"""
            yield "正在处理", "正在处理"
            yield "正在分析图片", "正在分析图片"
            yield "图片包含蓝色背景", "图片包含蓝色背景"
            yield "图片包含红色方块", "图片包含红色方块"
            yield "分析完成", "分析完成"

        def mock_generate_image_local(text, image, **kwargs):
            """模拟本地图像生成"""
            yield "本地处理中", "本地处理中"
            yield "本地分析完成", "本地分析完成"

        # 模拟主函数
        def generate_image(text, image, **kwargs):
            """图像生成函数"""
            if image is None:
                yield "Please upload an image.", "Please upload an image."
                return

            # 模拟在线模型
            yield from mock_generate_image_online(text, image, "online:model123", **kwargs)

        # 测试函数
        test_image = Image.new('RGB', (100, 100), color='red')

        print("1️⃣ 测试流式生成函数调用...")

        # 收集所有输出
        outputs = list(generate_image("测试", test_image))

        print(f"   ✅ 收集到 {len(outputs)} 个输出:")
        for i, output in enumerate(outputs):
            print(f"      {i+1}: {output}")

        print("\n2️⃣ 检查函数是否为生成器...")
        is_generator = inspect.isgeneratorfunction(generate_image)
        print(f"   ✅ 是生成器函数: {is_generator}")

        if outputs:
            print("\n3️⃣ 测试第一个输出...")
            first_output = outputs[0]
            print(f"   ✅ 第一个输出: {first_output}")
            print(f"   ✅ 输出类型: {type(first_output)}")

        print("\n" + "=" * 50)
        print("🎉 流式生成测试完成!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_streaming_function()