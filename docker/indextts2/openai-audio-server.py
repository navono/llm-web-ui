#!/usr/bin/env python3

import argparse
import base64
import os
import sys
import tempfile
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

# Configure logger
logger.remove()
logger.add(sys.stderr, level="TRACE")
logger.add("index-tts-server.log", rotation="10 MB", level="TRACE")


# Parse command-line arguments FIRST (before any other imports)
# This allows us to set environment variables before loading transformers
parser = argparse.ArgumentParser(
    description="OpenAI-compatible Audio API Server",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("--model_dir", type=str, default="/app/models", help="Model checkpoints directory")
parser.add_argument("--port", type=int, default=12234, help="Port to run the server on")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
parser.add_argument("--fp16", action="store_true", default=False, help="Use FP16 for inference")
parser.add_argument("--cuda_kernel", action="store_true", default=False, help="Use CUDA kernel for inference")
parser.add_argument("--deepspeed", action="store_true", default=False, help="Use DeepSpeed for acceleration")
parser.add_argument("--audio_prompt_dir", type=str, default="/app/audio_prompts", help="Audio prompt base directory")
parser.add_argument("--default_audio_prompt", type=str, default="Female-成熟_01.wav", help="Default audio prompt filename")
parser.add_argument("--offline", action="store_true", default=False, help="Run in offline mode (disable HuggingFace downloads)")
cmd_args = parser.parse_args()

# Set offline mode BEFORE importing any HuggingFace libraries
if cmd_args.offline:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    logger.info("Running in offline mode - HuggingFace downloads disabled")

audio_prompt_base_dir = cmd_args.audio_prompt_dir

logger.debug(f"Args: {cmd_args}")

# Validate model directory and required files (same as webui.py)
if not os.path.exists(cmd_args.model_dir):
    logger.error(f"Model directory {cmd_args.model_dir} does not exist. Please download the model first.")
    sys.exit(1)

for file in ["bpe.model", "gpt.pth", "config.yaml", "s2mel.pth", "wav2vec2bert_stats.pt"]:
    file_path = os.path.join(cmd_args.model_dir, file)
    if not os.path.exists(file_path):
        logger.error(f"Required file {file_path} does not exist. Please download it.")
        sys.exit(1)


# Add the index-tts package to the path if needed
index_tts_path = Path(__file__).parent / "index-tts"
if index_tts_path.exists():
    sys.path.append(str(index_tts_path))

# Import IndexTTS2
try:
    from indextts.infer_v2 import IndexTTS2
except ImportError as e:
    logger.error(f"Failed to import IndexTTS2: {e}")
    logger.error("Make sure index-tts is installed or in the Python path")
    sys.exit(1)

# Configure logger
logger.remove()
logger.add(sys.stderr, level="TRACE")
logger.add("index-tts-server.log", rotation="10 MB", level="TRACE")


default_audio_prompt_path = os.path.join(audio_prompt_base_dir, cmd_args.default_audio_prompt)

# Create FastAPI app
app = FastAPI(
    title="OpenAI-compatible Audio API",
    description="API for text-to-speech synthesis using OpenAI-compatible API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize IndexTTS2 model immediately (same as webui.py)
logger.info(f"Initializing IndexTTS2 model from {cmd_args.model_dir}...")
tts_instance = IndexTTS2(
    model_dir=cmd_args.model_dir,
    cfg_path=os.path.join(cmd_args.model_dir, "config.yaml"),
    use_fp16=cmd_args.fp16,
    use_deepspeed=cmd_args.deepspeed,
    use_cuda_kernel=cmd_args.cuda_kernel,
)
logger.info("IndexTTS2 model initialized successfully")


# Request models
class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    audio_prompt: str | None = Field(None, description="Base64-encoded audio prompt or path to audio file")
    output_format: str = Field("mp3", description="Output audio format (mp3 or wav)")
    max_text_tokens_per_sentence: int = Field(100, description="Maximum text tokens per sentence")
    sentences_bucket_max_size: int = Field(4, description="Maximum sentences per bucket")
    verbose: bool = Field(False, description="Enable verbose output")
    repetition_penalty: float = Field(10.0, description="Repetition penalty")
    top_p: float = Field(0.8, description="Top-p sampling parameter")
    top_k: int = Field(30, description="Top-k sampling parameter")
    temperature: float = Field(1.0, description="Sampling temperature")
    length_penalty: float = Field(0.0, description="Length penalty")
    num_beams: int = Field(3, description="Number of beams")
    max_mel_tokens: int = Field(600, description="Maximum mel tokens")
    do_sample: bool = Field(True, description="Do sample")
    voice: str | None = Field("lf", description="Local audio file")


class OpenAISpeechRequest(BaseModel):
    """OpenAI-compatible speech request model with IndexTTS2 extensions"""

    # Standard OpenAI parameters
    model: str = Field(default="indextts2", description="Model to use")
    input: str = Field(..., description="The text to generate audio for")
    voice: str = Field(default="", description="The voice to use")
    response_format: str = Field(default="mp3", description="The format of the audio output (mp3, opus, aac, flac, wav, pcm)")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="The speed of the generated audio (0.25 to 4.0)")

    # IndexTTS emotion control extensions
    emo_control_mode: int = Field(default=0, ge=0, le=3, description="Emotion control mode: 0=from speaker, 1=from reference audio, 2=from vector, 3=from text (experimental)")
    emo_reference_audio: str | None = Field(None, description="Emotion reference audio file path or base64")
    emo_weight: float = Field(default=0.65, ge=0.0, le=1.0, description="Emotion weight/alpha (0.0-1.0)")
    emo_vector: list[float] | None = Field(None, description="Emotion vector [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]")
    emo_text: str | None = Field(None, description="Emotion description text (experimental)")
    emo_random: bool = Field(default=False, description="Use random emotion sampling")

    # GPT2 sampling parameters
    do_sample: bool = Field(default=True, description="Whether to use sampling")
    temperature: float = Field(default=0.8, ge=0.1, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.8, ge=0.0, le=1.0, description="Top-p (nucleus) sampling")
    top_k: int = Field(default=30, ge=0, le=100, description="Top-k sampling (0 to disable)")
    num_beams: int = Field(default=3, ge=1, le=10, description="Number of beams for beam search")
    repetition_penalty: float = Field(default=10.0, ge=0.1, le=20.0, description="Repetition penalty")
    length_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Length penalty")
    max_mel_tokens: int = Field(default=1500, ge=50, le=3000, description="Maximum mel tokens to generate")

    # Sentence segmentation
    max_text_tokens_per_segment: int = Field(default=120, ge=20, le=500, description="Maximum text tokens per segment")

    # Other settings
    verbose: bool = Field(default=False, description="Enable verbose output")


# Helper functions
def get_tts_instance():
    """Get the IndexTTS2 instance (already initialized at module level)"""
    return tts_instance


async def process_audio_prompt(audio_prompt):
    """Process audio prompt from base64 or file path"""
    if not audio_prompt:
        return None

    logger.trace(f"audio prompt: {audio_prompt}")

    # Check if it's a base64 string
    if audio_prompt.startswith("data:") or ";base64," in audio_prompt:
        try:
            # Extract the base64 part if it's a data URL
            if ";base64," in audio_prompt:
                audio_prompt = audio_prompt.split(";base64,")[1]
                # Decode base64
                audio_data = base64.b64decode(audio_prompt)
            else:
                audio_data = audio_prompt

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                return temp_file.name
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio: {str(e)}") from e

    local_audio_path = os.path.join(audio_prompt_base_dir, audio_prompt)
    logger.trace(f"local audio path: {local_audio_path}")
    if os.path.exists(local_audio_path):
        temp_dir = tempfile.mkdtemp()
        with open(local_audio_path, "rb") as input_file:
            temp_audio_path = os.path.join(temp_dir, os.path.basename(local_audio_path))
            with open(temp_audio_path, "wb") as output_file:
                output_file.write(input_file.read())
        logger.info(f"Found audio prompt file at: {local_audio_path}, copy to temp path: {temp_audio_path}")
        return temp_audio_path
    else:
        logger.warning(f"Audio prompt file not found at: {local_audio_path}, use default audio prompt: {default_audio_prompt_path}")
        return default_audio_prompt_path


# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "IndexTTS2 OpenAI API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


def get_indexed_audio_files():
    """Get indexed audio files from available directories"""
    try:
        # 尝试列出多个可能的目录
        results = {}

        # 检查当前工作目录
        results["cwd"] = os.getcwd()

        # 尝试列出 audio_prompt 目录
        local_audio_path = audio_prompt_base_dir
        if os.path.exists(local_audio_path):
            files = os.listdir(local_audio_path)
            # 添加索引和文件名
            indexed_files = {str(i): filename for i, filename in enumerate(files)}
            results["audio_files"] = indexed_files
        else:
            results["audio_files"] = "Directory not found"

        return results
    except Exception as e:
        return {"error": str(e)}


@app.get("/v1/tts/voices")
async def list_audio_files():
    """Debug endpoint to list audio files in the audio_prompt directory"""
    return get_indexed_audio_files()


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible endpoint)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "indextts2",
                "object": "model",
                "created": 1677610602,
                "owned_by": "custom",
            }
        ],
    }


@app.get("/v1/voices")
async def list_voices():
    """List available voices (custom endpoint for voice discovery)"""
    # Get available audio files
    indexed_files = get_indexed_audio_files()

    # Standard OpenAI voices
    standard_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    # Custom voices from audio_prompt directory
    custom_voices = []
    if "audio_files" in indexed_files and isinstance(indexed_files["audio_files"], dict):
        custom_voices = list(indexed_files["audio_files"].values())

    return {
        "standard_voices": standard_voices,
        "custom_voices": custom_voices,
        "indexed_files": indexed_files.get("audio_files", {}),
    }


@app.post("/v1/tts")
async def tts_endpoint(request: TTSRequest, background_tasks: BackgroundTasks):
    """Generate speech from text"""
    try:
        # Get TTS instance
        tts = get_tts_instance()

        # Process audio prompt if provided

        audio_prompt_path = None
        if request.audio_prompt:
            audio_prompt_path = await process_audio_prompt(request.audio_prompt)
            background_tasks.add_task(lambda: os.unlink(audio_prompt_path) if audio_prompt_path and os.path.exists(audio_prompt_path) else None)
        elif request.voice:
            # 尝试使用索引获取音频文件
            try:
                # 获取索引音频文件列表
                indexed_files = get_indexed_audio_files()

                # 检查是否是特殊标识符
                if request.voice == "lf":
                    audio_prompt_path = os.path.join(audio_prompt_base_dir, "audo_enhanced_audio-lf2.mp3")
                # 检查是否是数字索引
                elif request.voice.isdigit():
                    # 尝试从本地目录获取
                    local_files = indexed_files.get("audio_files", {})
                    audio_prompt_path = os.path.join(audio_prompt_base_dir, local_files[request.voice]) if isinstance(local_files, dict) and request.voice in local_files else default_audio_prompt_path
                else:
                    # 直接使用文件名
                    audio_prompt_path = os.path.join(audio_prompt_base_dir, request.voice)
            except Exception as e:
                logger.error(f"Error finding voice by index: {e}")
                audio_prompt_path = default_audio_prompt_path
        else:
            audio_prompt_path = default_audio_prompt_path

        # 检查音频文件长度
        try:
            if audio_prompt_path and os.path.exists(audio_prompt_path):
                # 使用ffprobe检查音频文件长度
                import subprocess

                result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_prompt_path], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    try:
                        duration = float(result.stdout.strip())
                        logger.info(f"Audio prompt duration: {duration} seconds")

                        # 如果超过60秒，使用默认语音提示
                        if duration > 70.0:
                            logger.warning(f"Audio prompt too long ({duration} seconds), using default prompt")
                            audio_prompt_path = default_audio_prompt_path
                    except ValueError:
                        logger.warning(f"Could not parse duration: {result.stdout}")
                else:
                    logger.warning(f"Could not determine audio duration: {result.stderr}")

        except Exception as e:
            logger.warning(f"Error checking audio duration: {e}")
            # 出错时不替换音频文件，继续使用原文件

        logger.trace(f"prompt voice: {audio_prompt_path}")
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix=f".{request.output_format}", delete=False) as temp_file:
            output_path = temp_file.name

        # Add cleanup task
        background_tasks.add_task(lambda: os.unlink(output_path) if os.path.exists(output_path) else None)

        # Generate speech
        logger.info(f"Generating speech for text: {request.text[:50]}...")

        # 设置与成功案例相同的参数
        kwargs = {
            "do_sample": request.do_sample,
            "top_p": request.top_p,
            "top_k": request.top_k,
            "temperature": request.temperature,
            "length_penalty": request.length_penalty,
            "num_beams": request.num_beams,
            "repetition_penalty": request.repetition_penalty,
            "max_mel_tokens": request.max_mel_tokens,
            # "sentences_bucket_max_size": request.sentences_bucket_max_size,
        }

        # Use IndexTTS2.infer method
        logger.trace(f"spk_audio_prompt: {audio_prompt_path}")
        logger.trace(f"output_path: {output_path}")
        logger.trace(f"verbose: {request.verbose}")
        logger.trace(f"max_text_tokens_per_segment: {request.max_text_tokens_per_sentence}")
        logger.trace(f"kwargs: {kwargs}")
        tts.infer(spk_audio_prompt=audio_prompt_path, text=request.text, output_path=output_path, verbose=request.verbose, max_text_tokens_per_segment=request.max_text_tokens_per_sentence, **kwargs)

        # Stream the audio file
        def iterfile():
            with open(output_path, "rb") as f:
                yield from f

        content_type = "audio/mpeg" if request.output_format == "mp3" else "audio/wav"
        return StreamingResponse(iterfile(), media_type=content_type)

    except Exception as e:
        error_detail = {"error": str(e), "type": type(e).__name__}
        logger.error("Error in TTS generation: " + str(e))
        # Convert exception to string to ensure it's JSON serializable
        raise HTTPException(status_code=500, detail=error_detail) from e


# OpenAI-compatible endpoint
@app.post("/v1/audio/speech")
async def speech_endpoint(request: OpenAISpeechRequest, background_tasks: BackgroundTasks):
    """Generate speech from text (OpenAI-compatible API with IndexTTS2 extensions)

    This endpoint is compatible with OpenAI's /v1/audio/speech API and includes
    IndexTTS-specific extensions for emotion control and advanced generation settings.

    Args:
        request: OpenAI-compatible speech request with IndexTTS2 extensions

    Returns:
        StreamingResponse with audio data
    """
    try:
        # Validate input
        if not request.input or not request.input.strip():
            raise HTTPException(status_code=400, detail="Input text is required")

        # Normalize response format
        output_format = request.response_format.lower()
        if output_format not in ["mp3", "wav", "opus", "aac", "flac", "pcm"]:
            logger.warning(f"Unsupported format {output_format}, defaulting to mp3")
            output_format = "mp3"

        # Map common formats to supported ones
        format_mapping = {
            "opus": "mp3",
            "aac": "mp3",
            "flac": "wav",
            "pcm": "wav",
        }
        output_format = format_mapping.get(output_format, output_format)

        # Get TTS instance
        tts = get_tts_instance()

        # Process speaker audio prompt (voice)
        audio_prompt_path = None
        if request.voice:
            indexed_files = get_indexed_audio_files()
            if request.voice == "lf":
                audio_prompt_path = os.path.join(audio_prompt_base_dir, "audo_enhanced_audio-lf2.mp3")
            elif request.voice.isdigit():
                local_files = indexed_files.get("audio_files", {})
                audio_prompt_path = os.path.join(audio_prompt_base_dir, local_files[request.voice]) if isinstance(local_files, dict) and request.voice in local_files else default_audio_prompt_path
            else:
                audio_prompt_path = os.path.join(audio_prompt_base_dir, request.voice)
        else:
            audio_prompt_path = default_audio_prompt_path

        # Process emotion reference audio if provided
        emo_audio_prompt_path = None
        if request.emo_control_mode == 1 and request.emo_reference_audio:
            emo_audio_prompt_path = await process_audio_prompt(request.emo_reference_audio)
            if emo_audio_prompt_path:
                background_tasks.add_task(lambda: os.unlink(emo_audio_prompt_path) if os.path.exists(emo_audio_prompt_path) else None)

        # Process emotion vector if provided
        emo_vector = None
        if request.emo_control_mode == 2 and request.emo_vector:
            if len(request.emo_vector) == 8:
                emo_vector = tts.normalize_emo_vec(request.emo_vector, apply_bias=True)
            else:
                logger.warning(f"Invalid emotion vector length: {len(request.emo_vector)}, expected 8")

        # Process emotion text
        emo_text = request.emo_text if request.emo_text and request.emo_text.strip() else None

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as temp_file:
            output_path = temp_file.name

        background_tasks.add_task(lambda: os.unlink(output_path) if os.path.exists(output_path) else None)

        # Prepare generation kwargs
        kwargs = {
            "do_sample": request.do_sample,
            "top_p": request.top_p,
            "top_k": request.top_k if request.top_k > 0 else None,
            "temperature": request.temperature,
            "length_penalty": request.length_penalty,
            "num_beams": request.num_beams,
            "repetition_penalty": request.repetition_penalty,
            "max_mel_tokens": request.max_mel_tokens,
        }

        # Generate speech using IndexTTS2
        logger.info(f"Generating speech with emotion mode {request.emo_control_mode}")
        tts.infer(
            spk_audio_prompt=audio_prompt_path,
            text=request.input,
            output_path=output_path,
            emo_audio_prompt=emo_audio_prompt_path,
            emo_alpha=request.emo_weight,
            emo_vector=emo_vector,
            use_emo_text=(request.emo_control_mode == 3),
            emo_text=emo_text,
            use_random=request.emo_random,
            verbose=request.verbose,
            max_text_tokens_per_segment=request.max_text_tokens_per_segment,
            **kwargs,
        )

        # Stream the audio file
        def iterfile():
            with open(output_path, "rb") as f:
                yield from f

        content_type = "audio/mpeg" if output_format == "mp3" else "audio/wav"
        return StreamingResponse(iterfile(), media_type=content_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in speech endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    # Get port from environment or use command-line arg
    port = int(os.environ.get("PORT", cmd_args.port))
    host = os.environ.get("HOST", cmd_args.host)

    # Log server startup
    logger.info("Starting Audio OpenAI-compatible API server")
    logger.info(f"Model directory: {cmd_args.model_dir}")
    logger.info(f"FP16: {cmd_args.fp16}, CUDA kernel: {cmd_args.cuda_kernel}, DeepSpeed: {cmd_args.deepspeed}")
    logger.info(f"Server: {host}:{port}")

    # Start server
    uvicorn.run(app, host=host, port=port)
