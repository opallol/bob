# sync_gpt_local.py
# Tujuan:
# File ini menangani pemilihan engine antara GPT lokal dan GPT API (OpenAI) berdasarkan kompleksitas input.
# Jika input sederhana atau bersifat percakapan ringan, gunakan GPT lokal.
# Jika input memerlukan reasoning mendalam atau penuh konteks, gunakan GPT-4.1.
# File ini akan dipanggil dari router utama Bob untuk menentukan engine terbaik.

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from transformers import pipeline

GPT_LOCAL = pipeline("text-generation", model="tiiuae/falcon-7b-instruct", device=0)

def is_complex(text: str) -> bool:
    """Deteksi apakah input membutuhkan reasoning mendalam"""
    keywords = ["analisis", "bandingkan", "menurutmu", "jelaskan", "pendapat", "hubungan"]
    return any(k in text.lower() for k in keywords) or len(text.split()) > 35

def use_gpt_api(text: str) -> str:
    """Panggil GPT-4.1 via OpenAI API"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a reflective digital assistant named Bob."},
                {"role": "user", "content": text}
            ],
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[ERROR GPT-4.1]: {e}"

def use_gpt_local(text: str) -> str:
    """Gunakan GPT lokal untuk pertanyaan ringan"""
    try:
        result = GPT_LOCAL(text, max_length=256, do_sample=True)
        return result[0]['generated_text']
    except Exception as e:
        return f"[ERROR GPT-LOCAL]: {e}"

def route_model(text: str) -> str:
    """Router utama: pilih GPT lokal atau GPT-4.1"""
    if is_complex(text):
        return use_gpt_api(text)
    return use_gpt_local(text)