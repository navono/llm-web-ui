#!/usr/bin/env python3
"""
测试 book_speech.py 中的功能
"""

import sys
from pathlib import Path

import pytest
import requests
from unittest.mock import MagicMock, Mock, patch

# Add docker/indextts2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / "docker" / "indextts2"))

from book_speech import (
    AudioSpeechRequest,
    check_tts_service,
    create_tts_request,
    parse_ssml,
    verify_api_key,
)

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "test_audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API 配置
BOOK_SPEECH_API_URL = "http://localhost:12234/v1/book/speech"
API_KEY = "pingqixing"


def _check_service_available():
    """检查服务是否可用"""
    try:
        response = requests.get("http://localhost:12234/", timeout=2)
        return response.status_code in [200, 404]  # 404 也表示服务在运行
    except:
        return False


class TestVerifyApiKey:
    """测试 API key 验证"""

    def test_verify_api_key_valid(self):
        """测试有效的 API key"""
        assert verify_api_key("pingqixing") is True

    def test_verify_api_key_invalid(self):
        """测试无效的 API key"""
        assert verify_api_key("wrong_key") is False

    def test_verify_api_key_none(self):
        """测试 None API key"""
        assert verify_api_key(None) is False


class TestParseSSML:
    """测试 SSML 解析功能"""

    def test_parse_simple_ssml(self):
        """测试简单的 SSML"""
        ssml = """<speak>
            <voice name="zh-CN-XiaoxiaoNeural">
                <prosody rate="1.0">
                    这是测试文本
                </prosody>
            </voice>
        </speak>"""

        text, rate, voice = parse_ssml(ssml)

        assert text == "这是测试文本"
        assert rate == "1.0"
        assert voice == "zh-CN-XiaoxiaoNeural"

    def test_parse_ssml_with_speed_multiplier(self):
        """测试带速度倍数的 SSML"""
        ssml = """<speak>
            <voice name="zh-CN-YunxiNeural">
                <prosody rate="{{speakSpeed*2}}">
                    快速朗读的文本
                </prosody>
            </voice>
        </speak>"""

        text, rate, voice = parse_ssml(ssml)

        assert text == "快速朗读的文本"
        assert rate == "2"
        assert voice == "zh-CN-YunxiNeural"

    def test_parse_ssml_without_voice(self):
        """测试没有 voice 标签的 SSML"""
        ssml = """<speak>
            <prosody rate="1.5">
                没有声音标签的文本
            </prosody>
        </speak>"""

        text, rate, voice = parse_ssml(ssml)

        assert text == "没有声音标签的文本"
        assert rate == "1.5"
        assert voice is None

    def test_parse_ssml_without_prosody(self):
        """测试没有 prosody 标签的 SSML"""
        ssml = """<speak>
            <voice name="zh-CN-XiaoxiaoNeural">
                没有韵律标签的文本
            </voice>
        </speak>"""

        text, rate, voice = parse_ssml(ssml)

        assert text == "没有韵律标签的文本"
        assert rate == "1.0"  # 默认速率
        assert voice == "zh-CN-XiaoxiaoNeural"

    def test_parse_ssml_with_special_characters(self):
        """测试包含特殊字符的 SSML"""
        ssml = """<speak>
            <voice name="zh-CN-XiaoxiaoNeural">
                <prosody rate="1.0">
                    这是肏你妈的屄文本
                </prosody>
            </voice>
        </speak>"""

        text, rate, voice = parse_ssml(ssml)

        # 特殊字符应该被替换
        assert "操" in text
        assert "逼" in text
        assert "肏" not in text
        assert "屄" not in text

    def test_parse_ssml_invalid_format(self):
        """测试无效的 SSML 格式"""
        from fastapi import HTTPException

        ssml = "这不是有效的 SSML"

        with pytest.raises(HTTPException) as exc_info:
            parse_ssml(ssml)

        assert exc_info.value.status_code == 400
        assert "Invalid SSML format" in str(exc_info.value.detail)

    def test_parse_ssml_with_namespace(self):
        """测试带命名空间的 SSML"""
        ssml = """<mstts:speak xmlns:mstts="http://www.w3.org/2001/mstts">
            <mstts:voice name="zh-CN-XiaoxiaoNeural">
                <mstts:prosody rate="1.2">
                    带命名空间的文本
                </mstts:prosody>
            </mstts:voice>
        </mstts:speak>"""

        text, rate, voice = parse_ssml(ssml)

        assert text == "带命名空间的文本"
        assert rate == "1.2"
        assert voice == "zh-CN-XiaoxiaoNeural"


class TestCreateTTSRequest:
    """测试 TTS 请求创建"""

    def test_create_tts_request_basic(self):
        """测试基本的 TTS 请求创建"""
        text = "测试文本"
        rate = "1.0"

        request = create_tts_request(text, rate)

        assert isinstance(request, AudioSpeechRequest)
        assert request.input == text
        assert request.response_format == "mp3"
        assert request.speed == 1.0
        assert request.voice_file_path == "江疏影_60.mp3"

    def test_create_tts_request_with_percentage_rate(self):
        """测试带百分比速率的请求"""
        text = "测试文本"
        rate = "150%"

        request = create_tts_request(text, rate)

        assert request.speed == 1.5

    def test_create_tts_request_with_multiplier(self):
        """测试带倍数的请求"""
        text = "测试文本"
        rate = "2"

        request = create_tts_request(text, rate)

        assert request.speed == 2.0

    def test_create_tts_request_with_custom_voice(self):
        """测试自定义语音"""
        text = "测试文本"
        rate = "1.0"
        voice = "custom_voice.mp3"

        request = create_tts_request(text, rate, voice=voice)

        assert request.voice_file_path == voice

    def test_create_tts_request_with_wav_format(self):
        """测试 WAV 格式"""
        text = "测试文本"
        rate = "1.0"

        request = create_tts_request(text, rate, response_format="wav")

        assert request.response_format == "wav"

    def test_create_tts_request_invalid_rate(self):
        """测试无效的速率"""
        text = "测试文本"
        rate = "invalid"

        request = create_tts_request(text, rate)

        # 应该使用默认速率 1.0
        assert request.speed == 1.0


# Async test removed - check_tts_service is always True in openai-audio-server
# @pytest.mark.asyncio
# async def test_check_tts_service():
#     """测试 TTS 服务检查"""
#     result = await check_tts_service()
#     assert result is True


class TestAudioSpeechRequest:
    """测试 AudioSpeechRequest 模型"""

    def test_audio_speech_request_creation(self):
        """测试创建 AudioSpeechRequest"""
        request = AudioSpeechRequest(input="测试文本", response_format="mp3", speed=1.5, max_text_tokens_per_sentence=120, sentences_bucket_max_size=5, verbose=False, voice_file_path="test_voice.mp3")

        assert request.input == "测试文本"
        assert request.response_format == "mp3"
        assert request.speed == 1.5
        assert request.max_text_tokens_per_sentence == 120
        assert request.sentences_bucket_max_size == 5
        assert request.verbose is False
        assert request.voice_file_path == "test_voice.mp3"

    def test_audio_speech_request_defaults(self):
        """测试默认值"""
        request = AudioSpeechRequest(input="测试文本")

        assert request.response_format == "mp3"
        assert request.speed == 1.0
        assert request.max_text_tokens_per_sentence == 120
        assert request.sentences_bucket_max_size == 5
        assert request.verbose is False
        assert request.voice_file_path is None


@pytest.mark.skipif(
    not _check_service_available(),
    reason="IndexTTS2 service not available"
)
def test_http_api_integration():
    """通过 HTTP API 测试完整流程并保存音频"""
    test_cases = [
        ("basic_ssml", """<speak><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="1.0">这是基本的SSML测试文本。</prosody></voice></speak>""", "基本 SSML 格式"),
        ("speed_2x", """<speak><voice name="zh-CN-YunxiNeural"><prosody rate="{{speakSpeed*2}}">这是两倍速度的测试文本。</prosody></voice></speak>""", "2倍语速"),
        ("speed_150_percent", """<speak><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="150%">这是150%速度的测试文本。</prosody></voice></speak>""", "150% 语速"),
        ("chinese_text", """<speak><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="1.0">这是一段包含中文的测试文本，用于验证UTF-8编码是否正确处理。</prosody></voice></speak>""", "UTF-8 中文文本"),
    ]
    
    for name, ssml, description in test_cases:
        # 解析 SSML
        text, rate, voice = parse_ssml(ssml)
        tts_request = create_tts_request(text, rate, voice=voice)
        
        # 调用 HTTP API
        headers = {
            "ocp-apim-subscription-key": API_KEY,
            "Content-Type": "application/ssml+xml"
        }
        
        response = requests.post(
            BOOK_SPEECH_API_URL,
            data=ssml.encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        # 验证响应
        assert response.status_code == 200, f"API returned {response.status_code}: {response.text[:100]}"
        assert len(response.content) > 0, "Audio content is empty"
        assert response.headers.get('Content-Type') == 'audio/mpeg', f"Wrong content type: {response.headers.get('Content-Type')}"
        
        # 保存音频文件
        audio_file = OUTPUT_DIR / f"test_{name}.mp3"
        with open(audio_file, "wb") as f:
            f.write(response.content)
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
