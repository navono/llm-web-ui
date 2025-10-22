#!/usr/bin/env python3
"""Test script for STT configuration and service integration"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gradio.speech import load_stt_config


def test_load_stt_config():
    """Test loading STT configuration from config.yaml"""
    print("Testing STT configuration loading...")
    
    config = load_stt_config()
    
    print(f"\nLoaded STT Configuration:")
    print(f"  Service URL: {config['service_url'] or '(empty - will use online mode server)'}")
    print(f"  Default Model: {config['default_model']}")
    print(f"  Timeout: {config['timeout']} seconds")
    
    # Validate configuration
    assert isinstance(config, dict), "Config should be a dictionary"
    assert "service_url" in config, "Config should have service_url"
    assert "default_model" in config, "Config should have default_model"
    assert "timeout" in config, "Config should have timeout"
    
    print("\n✓ Configuration loaded successfully!")
    
    # Check if service URL is configured
    if config["service_url"]:
        print(f"\n✓ 独立 STT 服务已配置: {config['service_url']}")
        print("  Speech-to-Text 将使用配置的独立服务")
    else:
        print("\n✓ 使用 Online 模式的服务地址")
        print("  Speech-to-Text 将使用 online_client 的服务地址")
        print("  (即用户在 UI 中输入的服务器地址)")
    
    return config


if __name__ == "__main__":
    try:
        config = test_load_stt_config()
        
        print("\n" + "="*60)
        print("STT 配置测试总结")
        print("="*60)
        print(f"服务地址: {config['service_url'] or '使用 Online 模式服务器地址'}")
        print(f"默认模型: {config['default_model']}")
        print(f"超时时间: {config['timeout']}s")
        print("="*60)
        print("\n使用说明:")
        print("1. 如果 service_url 为空，STT 将使用 online 模式下用户输入的服务器地址")
        print("2. 如果需要使用独立的 STT 服务，请在 config.yaml 中配置 stt.service_url")
        print("3. 例如: service_url: 'http://localhost:12234/v1'")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
