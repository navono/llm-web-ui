#!/usr/bin/env python3
"""Test script for ASR transcription endpoint"""

import io
import wave

import numpy as np
import requests


def create_test_audio(duration_seconds=2, sample_rate=16000, frequency=440):
    """Create a simple test audio file (sine wave)"""
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    wav_buffer.seek(0)
    return wav_buffer.getvalue()


def test_transcription_endpoint(
    server_url="http://localhost:12234",
    audio_file_path=None,
    response_format="json"
):
    """Test the /v1/audio/transcriptions endpoint"""
    
    # Create or load audio
    if audio_file_path:
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        filename = audio_file_path
    else:
        audio_data = create_test_audio()
        filename = "test_audio.wav"
    
    # Prepare the request
    url = f"{server_url}/v1/audio/transcriptions"
    
    files = {
        'file': (filename, audio_data, 'audio/wav')
    }
    
    data = {
        'model': 'whisper-1',
        'response_format': response_format,
    }
    
    print(f"Testing transcription endpoint: {url}")
    print(f"Audio file: {filename}")
    print(f"Response format: {response_format}")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Request successful!")
            print("\nResponse:")
            if response_format == "text":
                print(response.text)
            else:
                print(response.json())
        else:
            print("✗ Request failed!")
            print(f"Error: {response.text}")
            
        return response
        
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed! Is the server running?")
        print(f"Make sure the server is started with: python openai-audio-server.py --enable_asr")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ASR transcription endpoint")
    parser.add_argument("--server", default="http://localhost:12234", help="Server URL")
    parser.add_argument("--audio", help="Path to audio file (optional, will generate test audio if not provided)")
    parser.add_argument("--format", default="json", choices=["json", "text", "verbose_json", "srt", "vtt"], help="Response format")
    
    args = parser.parse_args()
    
    test_transcription_endpoint(
        server_url=args.server,
        audio_file_path=args.audio,
        response_format=args.format
    )
