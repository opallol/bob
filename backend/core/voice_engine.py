# voice_engine.py
# Tujuan:
# File ini menyediakan fungsi untuk mengubah teks Bob menjadi suara (Text-to-Speech).
# Digunakan untuk meningkatkan kedekatan interaksi, terutama di WhatsApp dan interface suara.

import os
import logging
from gtts import gTTS
from datetime import datetime

VOICE_DIR = "static/voice"

def text_to_speech(text: str, filename: str = None) -> str:
    """Ubah teks menjadi file suara .mp3 dan kembalikan path-nya"""
    if not os.path.exists(VOICE_DIR):
        os.makedirs(VOICE_DIR)

    filename = filename or f"voice_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.mp3"
    filepath = os.path.join(VOICE_DIR, filename)

    try:
        tts = gTTS(text)
        tts.save(filepath)
    except Exception as e:
        logging.error(f"[TTS Error] Gagal mengubah teks jadi suara: {e}")
        return ""

    return filepath

def get_audio_path(filename: str) -> str:
    """Kembalikan path absolut ke file suara"""
    return os.path.join(VOICE_DIR, filename)