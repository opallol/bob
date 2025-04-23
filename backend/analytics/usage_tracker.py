# usage_tracker.py
# Tujuan:
# File ini berisi fungsi-fungsi analitik untuk melacak kontribusi pengguna terhadap memori Bob.
# Menghitung siapa saja yang paling sering mengajarkan pelajaran, serta topik apa yang diajarkan.
# Digunakan untuk insight internal Bob agar tahu siapa pengaruh terbesar dalam proses belajarnya.


from models import Memory
from sqlalchemy.orm import Session
from collections import Counter

def get_top_teachers(db: Session, limit=5):
    """Ambil nomor telepon yang paling banyak ngajarin Bob"""
    data = db.query(Memory.phone).all()
    counter = Counter(p[0] for p in data if p[0])
    return counter.most_common(limit)

def get_teacher_summary(db: Session):
    """Ringkasan jumlah pelajaran per phone dan topik"""
    data = db.query(Memory.phone, Memory.topik).all()
    result = {}
    for phone, topik in data:
        if phone not in result:
            result[phone] = {}
        if topik not in result[phone]:
            result[phone][topik] = 0
        result[phone][topik] += 1
    return result

def get_teacher_growth(db: Session):
    """Hitung total jumlah pelajaran yang diberikan oleh setiap phone"""
    data = db.query(Memory.phone).all()
    growth = {}
    for phone, in data:
        if phone:
            growth[phone] = growth.get(phone, 0) + 1
    return growth

def get_teacher_topics(db: Session, phone: str):
    """Ambil semua topik yang diajarkan oleh satu user tertentu"""
    records = db.query(Memory.topik).filter(Memory.phone == phone).all()
    return list(set(t[0] for t in records if t[0]))


# Fungsi untuk menghitung distribusi emosi dari pelajaran yang diberikan oleh masing-masing pengguna
def get_teacher_emotion_summary(db: Session):
    """Ringkasan emosi yang diajarkan oleh setiap pengguna"""
    data = db.query(Memory.phone, Memory.emotion).all()
    result = {}
    for phone, emotion in data:
        if not phone or not emotion:
            continue
        if phone not in result:
            result[phone] = {}
        if emotion not in result[phone]:
            result[phone][emotion] = 0
        result[phone][emotion] += 1
    return result


# Fungsi log_usage untuk mencatat interaksi user ke tabel usage_logs
from models import UsageLog
from datetime import datetime

def log_usage(user_id: str, input: str, output: str, db: Session, persona_context: str = None):
    """Catat interaksi pengguna dalam log penggunaan
    Returns True jika sukses, False jika gagal.
    """
    if not db:
        print("[ERROR] Session database tidak valid.")
        return False
    try:
        log = UsageLog(
            phone=user_id,
            input=input,
            output=output,
            tags=persona_context,  # ← ditambahkan untuk menyimpan persona context
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        print(f"[📈 USAGE] Log disimpan untuk {user_id}")
        return True
    except Exception as e:
        print(f"[ERROR] Gagal simpan usage log: {e}")
        return False