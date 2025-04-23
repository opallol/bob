

# reflection_utils.py
# Tujuan:
# File ini mendukung fitur refleksi harian Bob dengan menyediakan utilitas untuk
# membaca log refleksi, mencari refleksi tertentu berdasarkan tanggal, dan menghasilkan
# statistik sederhana dari log yang tersimpan.

import json
import os
from typing import Optional, List

REFLECTION_FILE = "logs/reflections.json"

def read_all_reflections() -> List[dict]:
    """Baca seluruh log refleksi dari file JSON"""
    if not os.path.exists(REFLECTION_FILE):
        return []
    with open(REFLECTION_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def get_reflection_by_date(date_str: str) -> Optional[dict]:
    """Ambil refleksi berdasarkan tanggal (format: YYYY-MM-DD)"""
    reflections = read_all_reflections()
    for entry in reflections:
        if entry.get("date") == date_str:
            return entry
    return None

def summarize_emotions() -> dict:
    """Hitung kemunculan emosi dari semua refleksi"""
    reflections = read_all_reflections()
    counter = {}
    for r in reflections:
        emotions = r.get("emotion_today", "").split(",")
        for emo in emotions:
            emo = emo.strip()
            if emo:
                counter[emo] = counter.get(emo, 0) + 1
    return counter
def write_reflection(reflection: dict):
    """Simpan refleksi baru ke file log"""
    reflections = read_all_reflections()
    reflections.append(reflection)
    with open(REFLECTION_FILE, "w") as f:
        json.dump(reflections, f, indent=2)