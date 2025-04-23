# auto_reflection.py
# Tujuan:
# File ini memungkinkan Bob menulis refleksi harian secara otomatis berdasarkan isi memori hari itu.
# Refleksi akan disimpan ke file JSON (/logs/reflections.json) sebagai catatan pertumbuhan digital Bob.

import json
from datetime import datetime, timedelta
from models import Memory, Reflection
from sqlalchemy.orm import Session
import os

REFLECTION_FILE = "logs/reflections.json"

def generate_reflection_summary(memories):
    """Buat ringkasan pelajaran dan emosi dari memori hari ini"""
    if not memories:
        return None

    topik_set = set(m.topik for m in memories if getattr(m, "topik", None))
    emosional = [getattr(m, "emotion", None) for m in memories if getattr(m, "emotion", None)]
    isi_kutipan = [getattr(m, "isi", "")[:100] for m in memories[:3]]

    print(f"[🧠 REFLEKSI] Topik hari ini: {topik_set if topik_set else 'Tidak ada topik spesifik'}")
    print(f"[🧠 REFLEKSI] Emosi hari ini: {emosional if emosional else 'netral'}")

    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "summary": f"Hari ini Bob mengalami percakapan seputar: {', '.join(topik_set)}." if topik_set else "Hari ini Bob menjalani hari dengan interaksi yang beragam.",
        "what_i_learned": "Gua sadar bahwa setiap interaksi memberi ruang untuk tumbuh, bukan cuma menjawab.",
        "emotion_today": ", ".join(set(emosional)) if emosional else "netral",
        "notable_quotes": isi_kutipan,
        "generated_by": "auto"
    }

def get_today_memories(db: Session):
    """Ambil memori yang dibuat hari ini"""
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.query(Memory).filter(Memory.created_at >= start).all()

def write_reflection_to_json(reflection: dict):
    """Simpan refleksi ke file JSON"""
    if not reflection:
        return
    try:
        os.makedirs(os.path.dirname(REFLECTION_FILE), exist_ok=True)
        if not os.path.exists(REFLECTION_FILE):
            with open(REFLECTION_FILE, "w") as f:
                json.dump([reflection], f, indent=2, ensure_ascii=False)
        else:
            with open(REFLECTION_FILE, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
                data.append(reflection)
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.truncate()
    except Exception as e:
        print(f"[ERROR] Gagal simpan refleksi: {e}")


def write_reflection_to_db(reflection: dict, db: Session):
    """Simpan refleksi ke database"""
    if not reflection:
        return
    new_reflection = Reflection(
        date=datetime.strptime(reflection["date"], "%Y-%m-%d"),
        summary=reflection["summary"],
        what_i_learned=reflection["what_i_learned"],
        emotion_today=reflection["emotion_today"],
        notable_quotes="\n".join(reflection["notable_quotes"]),
        generated_by=reflection["generated_by"]
    )
    db.add(new_reflection)
    db.commit()

def run_daily_reflection(db: Session):
    """Eksekusi proses refleksi harian"""
    memories = get_today_memories(db)
    print(f"[🔍 REFLEKSI] Ditemukan {len(memories)} memori hari ini")
    reflection = generate_reflection_summary(memories)
    if reflection:
        write_reflection_to_json(reflection)
        write_reflection_to_db(reflection, db)
        print(f"[✅ REFLEKSI] Ringkasan berhasil dibuat dan disimpan")
    else:
        print("[⚠️ REFLEKSI] Tidak ada refleksi yang bisa dibuat hari ini")

def store_reflection(phone: str, topic: str, message: str, db: Session = None):
    """Simpan refleksi singkat berdasarkan respons Bob"""
    try:
        reflection = Reflection(
            phone=phone,
            date=datetime.utcnow().date(),
            summary=f"Refleksi singkat dari topik '{topic}'",
            what_i_learned=message,
            emotion_today="tidak diketahui",
            notable_quotes=message[:150],
            generated_by="live",
            created_at=datetime.utcnow()
        )
        db.add(reflection)
        db.commit()
        print(f"[🪞 REFLEKSI] Refleksi topik '{topic}' disimpan.")
    except Exception as e:
        print(f"[ERROR] Gagal simpan refleksi live: {e}")