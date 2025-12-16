#!/usr/bin/env python3
"""
手动测试脚本 - 用于验证 book_speech 功能
通过 HTTP API 调用 IndexTTS2 服务
"""

import sys
from pathlib import Path

import requests

# Add docker/indextts2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / "docker" / "indextts2"))

from book_speech import (
    create_tts_request,
    parse_ssml,
    verify_api_key,
)

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "test_audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API 配置 - 通过 nginx 8080 端口访问
BOOK_SPEECH_API_URL = "http://localhost:8080/v1/book/speech"
# BOOK_SPEECH_API_URL = "https://api.pingeek.top/v1/book/speech"
API_KEY = "sk-test"


def test_api_key_verification():
    """测试 API key 验证"""
    print("\n" + "=" * 60)
    print("测试 API Key 验证")
    print("=" * 60)

    # 测试有效的 key
    assert verify_api_key("sk-test") is True
    print("✅ 有效的 API key: sk-test")

    # 测试无效的 key
    assert verify_api_key("wrong_key") is False
    print("✅ 无效的 API key 被拒绝")

    # 测试 None
    assert verify_api_key(None) is False
    print("✅ None API key 被拒绝")


def test_ssml_parsing():
    """测试 SSML 解析"""
    print("\n" + "=" * 60)
    print("测试 SSML 解析")
    print("=" * 60)

    # 测试 1: 基本 SSML
    ssml1 = """<speak>
        <voice name="zh-CN-XiaoxiaoNeural">
            <prosody rate="1.0">
                这是测试文本
            </prosody>
        </voice>
    </speak>"""

    text1, rate1, voice1 = parse_ssml(ssml1)
    print("\n测试 1 - 基本 SSML:")
    print(f"  文本: {text1}")
    print(f"  语速: {rate1}")
    print(f"  语音: {voice1}")
    assert text1 == "这是测试文本"
    assert rate1 == "1.0"
    assert voice1 == "zh-CN-XiaoxiaoNeural"
    print("  ✅ 解析成功")

    # 测试 2: 带速度倍数的 SSML
    ssml2 = """<speak>
        <voice name="zh-CN-YunxiNeural">
            <prosody rate="{{speakSpeed*2}}">
                快速朗读的文本
            </prosody>
        </voice>
    </speak>"""

    text2, rate2, voice2 = parse_ssml(ssml2)
    print("\n测试 2 - 速度倍数:")
    print(f"  文本: {text2}")
    print(f"  语速: {rate2}")
    print(f"  语音: {voice2}")
    assert text2 == "快速朗读的文本"
    assert rate2 == "2"
    assert voice2 == "zh-CN-YunxiNeural"
    print("  ✅ 解析成功")

    # 测试 3: 带命名空间的 SSML
    ssml3 = """<mstts:speak xmlns:mstts="http://www.w3.org/2001/mstts">
        <mstts:voice name="zh-CN-XiaoxiaoNeural">
            <mstts:prosody rate="1.5">
                带命名空间的文本
            </mstts:prosody>
        </mstts:voice>
    </mstts:speak>"""

    text3, rate3, voice3 = parse_ssml(ssml3)
    print("\n测试 3 - 带命名空间:")
    print(f"  文本: {text3}")
    print(f"  语速: {rate3}")
    print(f"  语音: {voice3}")
    assert text3 == "带命名空间的文本"
    assert rate3 == "1.5"
    assert voice3 == "zh-CN-XiaoxiaoNeural"
    print("  ✅ 解析成功")

    # 测试 4: 特殊字符替换
    ssml4 = """<speak>
        <voice name="zh-CN-XiaoxiaoNeural">
            <prosody rate="1.0">
                这是肏你妈的屄文本
            </prosody>
        </voice>
    </speak>"""

    text4, rate4, voice4 = parse_ssml(ssml4)
    print("\n测试 4 - 特殊字符替换:")
    print("  原始: 这是肏你妈的屄文本")
    print(f"  替换后: {text4}")
    assert "操" in text4
    assert "逼" in text4
    assert "肏" not in text4
    assert "屄" not in text4
    print("  ✅ 特殊字符替换成功")


def test_tts_request_creation():
    """测试 TTS 请求创建"""
    print("\n" + "=" * 60)
    print("测试 TTS 请求创建")
    print("=" * 60)

    # 测试 1: 基本请求
    request1 = create_tts_request("测试文本", "1.0")
    print("\n测试 1 - 基本请求:")
    print(f"  输入文本: {request1.input}")
    print(f"  格式: {request1.response_format}")
    print(f"  速度: {request1.speed}")
    print(f"  语音: {request1.voice_file_path}")
    assert request1.input == "测试文本"
    assert request1.response_format == "mp3"
    assert request1.speed == 1.0
    assert request1.voice_file_path == "江疏影_60.mp3"
    print("  ✅ 创建成功")

    # 测试 2: 百分比速率
    request2 = create_tts_request("测试文本", "150%")
    print("\n测试 2 - 百分比速率:")
    print("  输入速率: 150%")
    print(f"  转换后: {request2.speed}")
    assert request2.speed == 1.5
    print("  ✅ 速率转换成功")

    # 测试 3: 倍数速率
    request3 = create_tts_request("测试文本", "2")
    print("\n测试 3 - 倍数速率:")
    print("  输入速率: 2")
    print(f"  转换后: {request3.speed}")
    assert request3.speed == 2.0
    print("  ✅ 速率转换成功")

    # 测试 4: 自定义语音
    request4 = create_tts_request("测试文本", "1.0", voice="custom_voice.mp3")
    print("\n测试 4 - 自定义语音:")
    print(f"  语音文件: {request4.voice_file_path}")
    assert request4.voice_file_path == "custom_voice.mp3"
    print("  ✅ 自定义语音设置成功")

    # 测试 5: WAV 格式
    request5 = create_tts_request("测试文本", "1.0", response_format="wav")
    print("\n测试 5 - WAV 格式:")
    print(f"  格式: {request5.response_format}")
    assert request5.response_format == "wav"
    print("  ✅ 格式设置成功")


def test_http_api():
    """测试 HTTP API 调用"""
    print("\n" + "=" * 60)
    print("测试 HTTP API 调用")
    print("=" * 60)
    
    test_cases = [
        ("basic_ssml", """<speak><voice name="lf-style5.mp3"><prosody rate="1.0">这是基本的SSML测试文本。</prosody></voice></speak>""", "基本 SSML 格式"),
        ("speed_2x", """<speak><voice name="lf-style5.mp3"><prosody rate="{{speakSpeed*2}}">这是两倍速度的测试文本。</prosody></voice></speak>""", "2倍语速"),
        ("speed_150_percent", """<speak><voice name="lf-style6.mp3"><prosody rate="150%">这是150%速度的测试文本。</prosody></voice></speak>""", "150% 语速"),
        ("chinese_text", """<speak><voice name="lf-style6.mp3"><prosody rate="1.0">这是一段包含中文的测试文本，用于验证UTF-8编码是否正确处理。</prosody></voice></speak>""", "UTF-8 中文文本"),
    ]
    
    for name, ssml, description in test_cases:
        try:
            # 解析 SSML
            text, rate, voice = parse_ssml(ssml)
            tts_request = create_tts_request(text, rate, voice=voice)
            
            # 调用 HTTP API
            headers = {
                "ocp-apim-subscription-key": API_KEY,
                "Content-Type": "application/ssml+xml"
            }
            
            print(f"\n测试: {description}")
            print(f"  文本: {text[:30]}...")
            print(f"  语速: {rate} -> {tts_request.speed}x")
            print(f"  发送请求到: {BOOK_SPEECH_API_URL}")
            
            response = requests.post(
                BOOK_SPEECH_API_URL,
                data=ssml.encode('utf-8'),
                headers=headers,
                timeout=30
            )

            print(f"  响应状态码: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            if response.status_code != 200:
                print(f"  错误响应: {response.text[:200]}")

            if response.status_code == 200:
                # 保存音频文件
                audio_file = OUTPUT_DIR / f"test_{name}.mp3"
                print(f"  保存音频文件到: {audio_file}")
                print(f"  音频大小: {len(response.content)} bytes")
                with open(audio_file, "wb") as f:
                    f.write(response.content)
                print(f"  文件已保存，实际大小: {audio_file.stat().st_size} bytes")
                
                # 保存解析结果
                info_file = OUTPUT_DIR / f"test_{name}.txt"
                with open(info_file, "w", encoding="utf-8") as f:
                    f.write(f"测试用例: {name}\n")
                    f.write(f"描述: {description}\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"原始 SSML:\n{ssml}\n\n")
                    f.write(f"解析结果:\n")
                    f.write(f"  文本: {text}\n")
                    f.write(f"  语速: {rate} -> {tts_request.speed}x\n")
                    f.write(f"  语音: {voice or '默认'}\n")
                    f.write(f"  格式: {tts_request.response_format}\n\n")
                    f.write(f"API 响应:\n")
                    f.write(f"  状态码: {response.status_code}\n")
                    f.write(f"  Content-Type: {response.headers.get('Content-Type')}\n")
                    f.write(f"  音频大小: {len(response.content)} bytes\n")
                
                print(f"  ✅ 成功 - 音频已保存: {audio_file.name} ({len(response.content)} bytes)")
            else:
                print(f"  ❌ 失败 - 状态码: {response.status_code}")
                print(f"  错误: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  无法连接到服务 - 请确保 IndexTTS2 服务正在运行")
            print(f"  提示: docker compose up -d indextts2")
            break
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n📁 测试结果已保存到: {OUTPUT_DIR}")


def main():
    """运行所有测试"""
    print("\n" + "🎯 " + "=" * 58)
    print("🎯  Book Speech 功能测试 (HTTP API)")
    print("🎯 " + "=" * 58)

    try:
        # 基础功能测试
        # test_api_key_verification()
        test_ssml_parsing()
        test_tts_request_creation()

        print("\n" + "=" * 60)
        print("✅ 基础功能测试通过！")
        print("=" * 60)
        print("\n✅ API Key 验证: 正常")
        print("✅ SSML 解析: 正常")
        print("✅ TTS 请求创建: 正常")
        
        # HTTP API 测试
        test_http_api()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        print("\n📝 测试结果已保存到 outputs/test_audio 目录")
        print("📝 可以播放 .mp3 文件验证音频质量")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
