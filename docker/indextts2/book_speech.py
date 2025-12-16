import os
import re

import aiohttp
from fastapi import HTTPException
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel, Field

# Constants for TTS processing
DEFAULT_RATE = "1.0"
DEFAULT_TEXT = "测试文本"
MAX_TEXT_TOKENS = 120
SENTENCES_BUCKET_SIZE = 5
HTTP_OK = 200


class AudioSpeechRequest(BaseModel):
    """Audio speech request model"""

    input: str = Field(..., description="The text to generate audio for")
    response_format: str = Field(default="mp3", description="The format of the audio output")
    speed: float = Field(default=1.0, description="The speed of the generated audio")
    max_text_tokens_per_sentence: int = Field(default=120, description="Maximum text tokens per sentence")
    sentences_bucket_max_size: int = Field(default=5, description="Maximum sentences per bucket")
    verbose: bool = Field(default=False, description="Enable verbose output")
    voice_file_path: str | None = Field(None, description="Voice file path or identifier")
    voice: str | None = Field(None, description="Voice identifier")


def get_tts_service_url() -> str:
    """
    Get the URL for the TTS service.
    For the openai-audio-server, this should return the local service URL.
    """
    # Since we're running in the same service, we can use localhost
    # This function is here for compatibility with the forwarder version
    return os.environ.get("TTS_SERVICE_URL", "http://localhost:12234")


def verify_api_key(api_key: str) -> bool:
    if api_key is None:
        return False
    # Check against configured API keys
    valid_keys = [
        os.environ.get("API_KEY_1"),
        os.environ.get("API_KEY_2"),
        os.environ.get("API_KEY_3"),
    ]
    # Filter out None values
    valid_keys = [key for key in valid_keys if key]
    return api_key in valid_keys


def parse_ssml(body_text: str) -> tuple[str, str, str]:
    """
    Parse SSML content to extract text, speech rate, and voice.

    Args:
        body_text: The SSML content to parse

    Returns:
        Tuple containing (extracted_text, speech_rate, voice_name)
    """
    # Look for speak tag with or without namespace
    speak_match = re.search(r"<(?:\w+:)?speak[^>]*>(.*?)</(?:\w+:)?speak>", body_text, re.DOTALL)
    if not speak_match:
        logger.warning(f"Could not find speak tag in: {body_text}")
        # Try to extract any text content directly
        text_match = re.search(r"\{\{speakText\}\}(.*?)(?:</|$)", body_text, re.DOTALL)
        if text_match:
            # Found direct text content
            text = text_match.group(1).strip()
            rate = DEFAULT_RATE
            logger.info(f"Extracted text directly: {text}")
            return text, rate
        else:
            raise HTTPException(status_code=400, detail="Invalid SSML format: missing speak tag")

    speak_content = speak_match.group(1)

    # Extract voice information - capture all content inside voice tag
    voice_name = None
    voice_content = speak_content  # Default to full speak content

    # Try to extract voice information
    voice_match = re.search(r'<(?:\w+:)?voice[^>]*name=["\']([^"\']*)["\'](.*?)>(.*?)</(?:\w+:)?voice>', speak_content, re.DOTALL)
    if voice_match:
        voice_name = voice_match.group(1)
        # voice_attrs = voice_match.group(2)  # Additional voice attributes if any
        voice_content = voice_match.group(3)  # Content inside voice tags
        logger.debug(f"Extracted voice name: {voice_name}")

    # Extract prosody rate and content
    rate = DEFAULT_RATE
    prosody_content = None

    # Try to extract prosody information
    prosody_match = re.search(r'<(?:\w+:)?prosody[^>]*rate=["\']([^"\']*)["\'](.*?)>(.*?)</(?:\w+:)?prosody>', voice_content, re.DOTALL)
    if prosody_match:
        rate = prosody_match.group(1)
        prosody_content = prosody_match.group(3)
        # Handle special format like {{speakSpeed*4}}%
        if "{{" in rate and "}}" in rate:
            speed_match = re.search(r"\{\{speakSpeed\*(\d+(?:\.\d+)?)\}\}", rate)
            if speed_match:
                rate = speed_match.group(1)

    # Determine the text content - prioritize content from innermost tag
    raw_text = prosody_content if prosody_content is not None else voice_content

    # Extract actual text content (remove any remaining XML tags)
    text = re.sub(r"<[^>]+>", "", raw_text)
    text = re.sub(r"\{\{speakText\}\}", "", text)  # Remove {{speakText}} placeholder
    text = text.strip()

    # If text is still empty, try to extract any text content from the full SSML
    if not text:
        # Extract all text between any tags
        all_text_parts = re.findall(r">([^<]+)<", body_text)
        text = " ".join(part.strip() for part in all_text_parts if part.strip())
        text = text.strip()

    # If still empty, use a default text
    if not text:
        text = DEFAULT_TEXT
        logger.warning(f"Could not extract text from SSML, using default text: {text}")

    text = text.replace("肏", "操").replace("屄", "逼")
    logger.debug(f"Extracted text: {text}, rate: {rate}, voice: {voice_name}")
    return text, rate, voice_name


async def check_tts_service() -> bool:
    """
    Check if the TTS service is available.
    For the openai-audio-server, we assume it's always available since we're in the same process.
    """
    return True


def create_tts_request(text: str, rate: str, response_format: str = "mp3", voice: str = None) -> AudioSpeechRequest:
    """
    Create an AudioSpeechRequest object from text and rate.

    Args:
        text: The text to convert to speech
        rate: The speech rate as a string (may include % or be a multiplier)
        response_format: The desired audio format (default: mp3)
        voice: The voice name or index to use (default: None)

    Returns:
        AudioSpeechRequest object ready for TTS processing
    """
    # Convert rate to speed parameter (rate is usually a percentage or multiplier)
    try:
        # Remove % if present and convert to float
        speed = float(rate.replace("%", "")) / 100.0 if isinstance(rate, str) and "%" in rate else float(rate)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse rate '{rate}' as float, using default speed 1.0")
        speed = 1.0

    # Create TTS request
    return AudioSpeechRequest(
        input=text,
        response_format=response_format,
        speed=speed,
        max_text_tokens_per_sentence=MAX_TEXT_TOKENS,
        sentences_bucket_max_size=SENTENCES_BUCKET_SIZE,
        verbose=False,
        voice_file_path=voice if voice else "江疏影_60.mp3",
    )


async def perform_tts_inference(tts_request: AudioSpeechRequest, audio_prompt: str = None) -> Response:
    """
    Forward TTS request to docker-index-tts service and return the audio response.
    """

    try:
        # Prepare request payload for docker-index-tts service based on the provided test script format
        # 确保中文文本被正确处理
        input_text = tts_request.input

        # 检查是否包含中文字符
        # has_chinese = any("一" <= char <= "鿿" for char in input_text)
        # if has_chinese:
        #     logger.info("Detected Chinese text in the request")

        payload = {
            "text": input_text,
            "response_format": {"type": tts_request.response_format.lower()},
            "max_text_tokens_per_sentence": tts_request.max_text_tokens_per_sentence,
            "sentences_bucket_max_size": tts_request.sentences_bucket_max_size,
            "verbose": tts_request.verbose,
        }

        # Add audio prompt if provided
        if audio_prompt:
            # If audio_prompt is a numeric index, pass it as voice parameter
            if isinstance(audio_prompt, str) and audio_prompt.isdigit():
                payload["voice"] = audio_prompt
            else:
                payload["audio_prompt"] = audio_prompt

        # Add speed parameter if provided
        if tts_request.speed is not None:
            payload["speed"] = tts_request.speed

        # Send request to docker-index-tts service
        base_url = get_tts_service_url()
        # logger.trace(f"TTS url: {base_url}")
        # 使用ClientSession时指定正确的编码处理
        async with aiohttp.ClientSession() as session, session.post(f"{base_url}/v1/tts", json=payload, headers={"Content-Type": "application/json; charset=utf-8"}) as response:
            if response.status != HTTP_OK:
                error_detail = await response.text()
                logger.error(f"TTS service returned error: {response.status}, {error_detail}")
                raise HTTPException(status_code=response.status, detail=f"TTS service error: {error_detail}")

            # Get content type from response headers
            content_type = response.headers.get("Content-Type", "audio/mpeg")

            # Read response content
            audio_data = await response.read()

            # Return audio response
            return Response(content=audio_data, media_type=content_type)

    except aiohttp.ClientError as e:
        logger.error(f"Failed to connect to TTS service: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to TTS service: {str(e)}") from e
    except Exception as e:
        logger.error(f"TTS inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS inference failed: {str(e)}") from e
