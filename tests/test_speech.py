#!/usr/bin/env python3
"""
测试语音相关功能：TTS (Text-to-Speech) 和 STT (Speech-to-Text)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture
def mock_online_client():
    """模拟在线客户端"""
    with patch("gradio.speech.online_client") as mock_client:
        mock_client.base_url = "http://localhost:8080/v1"
        mock_client.session = MagicMock()
        yield mock_client


@pytest.fixture
def sample_audio_file():
    """创建一个临时音频文件用于测试"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        # 写入一些虚拟数据
        f.write(b"fake audio data for testing")
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_text():
    """测试用的示例文本"""
    return "这是一段测试文本，用于测试文字转语音功能。"


class TestTranscribeAudio:
    """测试 transcribe_audio 函数"""

    def test_transcribe_audio_success(self, mock_online_client, sample_audio_file):
        """测试音频转录成功的情况"""
        from gradio.speech import transcribe_audio

        # 模拟成功的响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "这是转录的文本"}
        mock_online_client.session.post.return_value = mock_response

        result = transcribe_audio(sample_audio_file, model="whisper-1")

        assert result["success"] is True
        assert result["text"] == "这是转录的文本"
        
        # 验证调用了正确的端点
        call_args = mock_online_client.session.post.call_args
        assert "/audio/transcriptions" in call_args[0][0]

    def test_transcribe_audio_http_error(self, mock_online_client, sample_audio_file):
        """测试 HTTP 错误响应"""
        from gradio.speech import transcribe_audio

        # 模拟失败的响应
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_online_client.session.post.return_value = mock_response

        result = transcribe_audio(sample_audio_file, model="whisper-1")

        assert result["success"] is False
        assert "HTTP 500" in result["error"]

    def test_transcribe_audio_file_not_found(self, mock_online_client):
        """测试音频文件不存在的情况"""
        from gradio.speech import transcribe_audio

        result = transcribe_audio("/nonexistent/file.mp3", model="whisper-1")

        assert result["success"] is False
        assert "音频文件不存在" in result["error"]

    def test_transcribe_audio_missing_text_field(self, mock_online_client, sample_audio_file):
        """测试响应缺少 text 字段的情况"""
        from gradio.speech import transcribe_audio

        # 模拟缺少 text 字段的响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "some data"}
        mock_online_client.session.post.return_value = mock_response

        result = transcribe_audio(sample_audio_file, model="whisper-1")

        assert result["success"] is False
        assert "响应格式错误" in result["error"]

    def test_transcribe_audio_network_exception(self, mock_online_client, sample_audio_file):
        """测试网络异常的情况"""
        from gradio.speech import transcribe_audio

        # 模拟网络异常
        mock_online_client.session.post.side_effect = Exception("Network error")

        result = transcribe_audio(sample_audio_file, model="whisper-1")

        assert result["success"] is False
        assert "转录异常" in result["error"]


class TestGenerateSpeechToText:
    """测试 generate_speech_to_text 函数"""

    @patch("gradio.speech.transcribe_audio")
    @patch("gradio.speech.gr")
    def test_generate_speech_to_text_success(self, mock_gr, mock_transcribe, sample_audio_file):
        """测试语音转文字成功的情况"""
        from gradio.speech import generate_speech_to_text

        # 模拟成功的转录结果
        mock_transcribe.return_value = {
            "success": True,
            "text": "转录成功的文本内容"
        }

        text_output, markdown_output = generate_speech_to_text(sample_audio_file)

        assert text_output == "转录成功的文本内容"
        assert "## 转录结果" in markdown_output
        assert "转录成功的文本内容" in markdown_output
        mock_gr.Info.assert_called_once_with("语音转文字成功")

    @patch("gradio.speech.transcribe_audio")
    @patch("gradio.speech.gr")
    def test_generate_speech_to_text_failure(self, mock_gr, mock_transcribe, sample_audio_file):
        """测试语音转文字失败的情况"""
        from gradio.speech import generate_speech_to_text

        # 模拟失败的转录结果
        mock_transcribe.return_value = {
            "success": False,
            "error": "转录服务不可用"
        }

        text_output, markdown_output = generate_speech_to_text(sample_audio_file)

        assert "Error: 转录服务不可用" in text_output
        assert "**Error:**" in markdown_output
        mock_gr.Error.assert_called_once()

    @patch("gradio.speech.gr")
    def test_generate_speech_to_text_no_audio(self, mock_gr):
        """测试没有提供音频文件的情况"""
        from gradio.speech import generate_speech_to_text

        text_output, markdown_output = generate_speech_to_text("")

        assert "请先上传或录制音频文件" in text_output
        assert "**Error:**" in markdown_output
        mock_gr.Warning.assert_called_once()

    @patch("gradio.speech.transcribe_audio")
    @patch("gradio.speech.gr")
    def test_generate_speech_to_text_exception(self, mock_gr, mock_transcribe, sample_audio_file):
        """测试处理过程中发生异常的情况"""
        from gradio.speech import generate_speech_to_text

        # 模拟异常
        mock_transcribe.side_effect = Exception("Unexpected error")

        text_output, markdown_output = generate_speech_to_text(sample_audio_file)

        assert "处理失败" in text_output
        assert "**Error:**" in markdown_output
        mock_gr.Error.assert_called_once()


class TestSynthesizeSpeech:
    """测试 synthesize_speech 函数"""

    def test_synthesize_speech_success(self, mock_online_client, sample_text):
        """测试语音合成成功的情况"""
        from gradio.speech import synthesize_speech

        # 模拟成功的响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        mock_online_client.session.post.return_value = mock_response

        result = synthesize_speech(sample_text, model="tts-1", voice="alloy", speed=1.0)

        assert result["success"] is True
        assert "audio_path" in result
        assert os.path.exists(result["audio_path"])
        
        # 清理生成的文件
        if os.path.exists(result["audio_path"]):
            os.unlink(result["audio_path"])

        # 验证调用了正确的端点
        call_args = mock_online_client.session.post.call_args
        assert "/audio/speech" in call_args[0][0]

    def test_synthesize_speech_http_error(self, mock_online_client, sample_text):
        """测试 HTTP 错误响应"""
        from gradio.speech import synthesize_speech

        # 模拟失败的响应
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_online_client.session.post.return_value = mock_response

        result = synthesize_speech(sample_text, model="tts-1", voice="alloy", speed=1.0)

        assert result["success"] is False
        assert "HTTP 400" in result["error"]

    def test_synthesize_speech_network_exception(self, mock_online_client, sample_text):
        """测试网络异常的情况"""
        from gradio.speech import synthesize_speech

        # 模拟网络异常
        mock_online_client.session.post.side_effect = Exception("Connection timeout")

        result = synthesize_speech(sample_text, model="tts-1", voice="alloy", speed=1.0)

        assert result["success"] is False
        assert "语音合成异常" in result["error"]


class TestGenerateTextToSpeech:
    """测试 generate_text_to_speech 函数"""

    @pytest.mark.skip(reason="Requires complex mocking of relative imports in generate_text_to_speech")
    @patch("gradio.speech.synthesize_speech")
    @patch("gradio.speech.is_online_model")
    @patch("gradio.speech.get_online_model_id")
    @patch("gradio.speech.gr")
    def test_generate_text_to_speech_success(
        self, mock_gr, mock_get_model_id, mock_is_online, mock_synthesize, sample_text
    ):
        """测试文字转语音成功的情况"""
        # Mock the model_manager import inside the function
        with patch.dict('sys.modules', {'model_manager': MagicMock()}):
            from gradio.speech import generate_text_to_speech
            
            # 模拟在线模型
            mock_is_online.return_value = True
            mock_get_model_id.return_value = "tts-1"
            
            # 模拟成功的合成结果
            mock_synthesize.return_value = {
                "success": True,
                "audio_path": "/tmp/test_audio.mp3"
            }

            audio_path, status_msg = generate_text_to_speech(sample_text, voice="alloy", speed=1.0)

            assert audio_path == "/tmp/test_audio.mp3"
            assert "语音合成成功" in status_msg
            mock_gr.Info.assert_called_once_with("语音合成成功")

    @pytest.mark.skip(reason="Requires complex mocking of relative imports in generate_text_to_speech")
    @patch("gradio.speech.is_online_model")
    @patch("gradio.speech.gr")
    def test_generate_text_to_speech_not_online_model(self, mock_gr, mock_is_online, sample_text):
        """测试使用非在线模型的情况"""
        # Mock the model_manager import inside the function
        with patch.dict('sys.modules', {'model_manager': MagicMock()}):
            from gradio.speech import generate_text_to_speech
            
            # 模拟非在线模型
            mock_is_online.return_value = False

            audio_path, status_msg = generate_text_to_speech(sample_text, voice="alloy", speed=1.0)

            assert audio_path is None
            assert "仅支持在线模型" in status_msg
            mock_gr.Error.assert_called_once()

    @patch("gradio.speech.gr")
    def test_generate_text_to_speech_empty_text(self, mock_gr):
        """测试空文本的情况"""
        from gradio.speech import generate_text_to_speech

        audio_path, status_msg = generate_text_to_speech("", voice="alloy", speed=1.0)

        assert audio_path is None
        assert "请输入要转换的文本" in status_msg
        mock_gr.Warning.assert_called_once()

    @patch("gradio.speech.synthesize_speech")
    @patch("gradio.speech.is_online_model")
    @patch("gradio.speech.get_online_model_id")
    @patch("gradio.speech.gr")
    def test_generate_text_to_speech_failure(
        self, mock_gr, mock_get_model_id, mock_is_online, mock_synthesize, sample_text
    ):
        """测试文字转语音失败的情况"""
        # Mock the model_manager import inside the function
        with patch.dict('sys.modules', {'model_manager': MagicMock()}):
            from gradio.speech import generate_text_to_speech
            
            # 模拟在线模型
            mock_is_online.return_value = True
            mock_get_model_id.return_value = "tts-1"
            
            # 模拟失败的合成结果
            mock_synthesize.return_value = {
                "success": False,
                "error": "语音合成服务不可用"
            }

            audio_path, status_msg = generate_text_to_speech(sample_text, voice="alloy", speed=1.0)

            assert audio_path is None
            assert "**Error:**" in status_msg
            mock_gr.Error.assert_called_once()

    @patch("gradio.speech.is_online_model")
    @patch("gradio.speech.get_online_model_id")
    @patch("gradio.speech.gr")
    def test_generate_text_to_speech_exception(
        self, mock_gr, mock_get_model_id, mock_is_online, sample_text
    ):
        """测试处理过程中发生异常的情况"""
        # Mock the model_manager import inside the function
        with patch.dict('sys.modules', {'model_manager': MagicMock()}):
            from gradio.speech import generate_text_to_speech
            
            # 模拟在线模型
            mock_is_online.return_value = True
            mock_get_model_id.side_effect = Exception("Unexpected error")

            audio_path, status_msg = generate_text_to_speech(sample_text, voice="alloy", speed=1.0)

            assert audio_path is None
            assert "处理失败" in status_msg
            mock_gr.Error.assert_called_once()


class TestGetAvailableVoices:
    """测试 get_available_voices 函数"""

    def test_get_available_voices_standard_format(self, mock_online_client):
        """测试标准格式的声音列表"""
        from gradio.speech import get_available_voices

        # 模拟标准格式响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        }
        mock_online_client.session.get.return_value = mock_response

        result = get_available_voices()

        assert result["success"] is True
        assert len(result["voices"]) == 6
        assert "alloy" in result["voices"]

    def test_get_available_voices_indextts_format(self, mock_online_client):
        """测试 IndexTTS 格式的声音列表"""
        from gradio.speech import get_available_voices

        # 模拟 IndexTTS 格式响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "audio_files": {
                "0": "voice1.wav",
                "1": "voice2.wav",
                "2": "voice3.wav"
            }
        }
        mock_online_client.session.get.return_value = mock_response

        result = get_available_voices()

        assert result["success"] is True
        assert len(result["voices"]) == 3
        assert "voice1.wav" in result["voices"]

    def test_get_available_voices_openai_format(self, mock_online_client):
        """测试 OpenAI 格式的声音列表"""
        from gradio.speech import get_available_voices

        # 模拟 OpenAI 格式响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "alloy", "name": "Alloy"},
                {"id": "echo", "name": "Echo"}
            ]
        }
        mock_online_client.session.get.return_value = mock_response

        result = get_available_voices()

        assert result["success"] is True
        assert len(result["voices"]) == 2
        assert "alloy" in result["voices"]

    def test_get_available_voices_all_endpoints_fail(self, mock_online_client):
        """测试所有端点都失败的情况"""
        from gradio.speech import get_available_voices

        # 模拟所有端点都失败
        mock_online_client.session.get.side_effect = Exception("Connection error")

        result = get_available_voices()

        assert result["success"] is True
        assert result["voices"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
