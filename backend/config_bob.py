# config.py
# Tujuan:
# File ini menyimpan seluruh konfigurasi utama Bob secara terpusat,
# termasuk pengambilan API key, model GPT yang digunakan, dan mode aktif Bob (reflektif, suara, lokal).
# Digunakan oleh seluruh modul untuk menjaga konsistensi sistem dan memudahkan perubahan.

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # jika pakai TTS eksternal

# Model
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4.1-nano")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# Mode
REFLECTIVE_MODE = os.getenv("REFLECTIVE_MODE", "true").lower() == "true"
VOICE_MODE = os.getenv("VOICE_MODE", "false").lower() == "true"
GPT_MODE = os.getenv("GPT_MODE", "auto")  # auto, local, api
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Path
REFLECTION_FILE = "logs/reflections.json"
VECTOR_STORE_PATH = "data/vector_store.faiss"

# Voice Output
VOICE_OUTPUT_DIR = "static/voice"
