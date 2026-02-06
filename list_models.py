
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv('.env_config')

api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("No API key")
    exit(1)

genai.configure(api_key=api_key)

print("Listing supported models...")
for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(f"Embedding Model: {m.name}")
    elif 'generateContent' in m.supported_generation_methods:
        print(f"Generative Model: {m.name}")
