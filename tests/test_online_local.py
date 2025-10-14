#!/usr/bin/env python3
"""
测试本地Online模式功能
"""

import sys
sys.path.append('src')

def test_online_functions():
    """测试Online模式的功能"""
    print("🧪 测试Online模式功能")
    print("=" * 50)

    try:
        # 测试导入
        print("1️⃣ 测试模块导入...")
        from gradio.online_client import OnlineClient, connect_to_server
        from gradio.text_generation import switch_model, generate_text
        print("   ✅ 模块导入成功")

        # 测试连接函数
        print("\n2️⃣ 测试连接到localhost:18800...")
        result = connect_to_server("http://localhost:18800/v1")

        if result["success"]:
            print(f"   ✅ {result['message']}")
            print(f"   📝 发现 {len(result['models'])} 个在线模型:")
            for model in result['models']:
                print(f"      - {model[0]}")
        else:
            print(f"   ❌ {result['message']}")
            return False

        # 测试模型切换
        print("\n3️⃣ 测试切换到在线模型...")
        if result['models']:
            online_model_key = result['models'][0][1]  # 获取第一个在线模型
            switch_result = switch_model(online_model_key)
            print(f"   {switch_result}")

            # 测试文本生成
            print("\n4️⃣ 测试在线文本生成...")
            generated_text = ""
            for chunk in generate_text("你好，请简单介绍一下自己。", max_new_tokens=30):
                generated_text = chunk
                print(f"   📤 生成中: {chunk}")

            print(f"   ✅ 生成完成: {generated_text}")
        else:
            print("   ⚠️ 没有在线模型可供测试")

        print("\n" + "=" * 50)
        print("🎉 Online模式测试完成!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_online_functions()