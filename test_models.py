#!/usr/bin/env python3
"""Test script to check available Gemini models."""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv('.env_config')

api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ No GOOGLE_API_KEY found")
    exit(1)

genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    print("Available models:")
    for model in models:
        if 'gemini' in model.name:
            print(f"  - {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")