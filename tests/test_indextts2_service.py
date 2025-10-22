#!/usr/bin/env python3
"""Test IndexTTS2 service"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_indextts2_service_import():
    """Test that IndexTTS2Service can be imported"""
    print("Testing IndexTTS2Service import...")
    
    try:
        from services.indextts2 import IndexTTS2Service
        print("✓ IndexTTS2Service imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import IndexTTS2Service: {e}")
        return False


def test_model_availability_check():
    """Test model availability checking"""
    print("\nTesting model availability check...")
    
    try:
        from services.indextts2 import IndexTTS2Service
        
        # Test with non-existent directory
        is_available, missing = IndexTTS2Service.check_model_availability("./non_existent")
        print(f"✓ Non-existent directory check: available={is_available}")
        
        # Test with checkpoints directory
        is_available, missing = IndexTTS2Service.check_model_availability("./checkpoints")
        if is_available:
            print("✓ Model files found in ./checkpoints")
        else:
            print(f"⚠ Model files missing in ./checkpoints: {missing}")
        
        return True
    except Exception as e:
        print(f"✗ Model availability check failed: {e}")
        return False


def test_package_availability():
    """Test package availability checking"""
    print("\nTesting package availability check...")
    
    try:
        from services.indextts2 import IndexTTS2Service
        
        is_available = IndexTTS2Service.is_package_available()
        if is_available:
            print("✓ IndexTTS2 package is installed")
        else:
            print("⚠ IndexTTS2 package not installed (this is OK)")
        
        return True
    except Exception as e:
        print(f"✗ Package availability check failed: {e}")
        return False


def test_service_creation():
    """Test service instance creation"""
    print("\nTesting service creation...")
    
    try:
        from services.indextts2 import IndexTTS2Service
        
        service = IndexTTS2Service(
            model_dir="./checkpoints",
            use_fp16=False,
            use_deepspeed=False,
            use_cuda_kernel=False,
        )
        print("✓ IndexTTS2Service instance created")
        print(f"  - Model directory: {service.model_dir}")
        print(f"  - Is available: {service.is_available}")
        
        return True
    except Exception as e:
        print(f"✗ Service creation failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("IndexTTS2 Service Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Import", test_indextts2_service_import()))
    results.append(("Model availability", test_model_availability_check()))
    results.append(("Package availability", test_package_availability()))
    results.append(("Service creation", test_service_creation()))
    
    print()
    print("=" * 60)
    print("Test Results")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
