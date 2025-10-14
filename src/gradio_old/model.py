"""Model management and configuration for the Gradio interface."""

import os

import torch
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

from ..utils import CustomizeLogger
from ..utils.config import Config

# Initialize logger
gen_config = Config().get_config()
logger = CustomizeLogger.make_logger(gen_config["log"])

# Configuration constants
MAX_MAX_NEW_TOKENS = 4096
DEFAULT_MAX_NEW_TOKENS = 1024
MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507-FP8"

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def print_device_info():
    """Print device and CUDA information for debugging."""
    logger.info("CUDA_VISIBLE_DEVICES=%s", os.environ.get("CUDA_VISIBLE_DEVICES"))
    logger.info("torch.__version__ = %s", torch.__version__)
    logger.info("torch.version.cuda = %s", torch.version.cuda)
    logger.info("cuda available: %s", torch.cuda.is_available())
    logger.info("cuda device count: %s", torch.cuda.device_count())
    if torch.cuda.is_available():
        logger.info("current device: %s", torch.cuda.current_device())
        logger.info("device name: %s", torch.cuda.get_device_name(torch.cuda.current_device()))
    logger.info("Using device: %s", device)


def load_models():
    """Load and initialize the models."""
    logger.info("Loading model: %s", MODEL_ID)
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True, use_fast=False)

    # Load model with proper device mapping
    model = Qwen2VLForConditionalGeneration.from_pretrained(MODEL_ID, trust_remote_code=True, device_map="auto" if torch.cuda.is_available() else "cpu", torch_dtype=torch.float16).eval()

    logger.info("Model loaded successfully")
    return processor, model


# Global model variables
processor_q3vl = None
model_q3vl = None


def initialize_models():
    """Initialize models if not already loaded."""
    global processor_q3vl, model_q3vl
    if processor_q3vl is None or model_q3vl is None:
        print_device_info()
        processor_q3vl, model_q3vl = load_models()
    return processor_q3vl, model_q3vl


# Initialize models on module import
initialize_models()
