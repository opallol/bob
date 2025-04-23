from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
# memory_engine.py
# Tujuan:
# Modul ini merupakan pusat logika untuk menyimpan, mengambil,
# dan menyusun ulang memori Bob berdasarkan percakapan, pengajaran, dan refleksi.
# Ini menjembatani komunikasi antara API dan database ORM.

from sqlalchemy.orm import Session
from models import Memory
import pickle
from datetime import datetime, timezone
from typing import Optional
from core.embedding import get_embedding

def save_memory(db: Session, phone: str, kode_satker: str, topik: str, isi: str,
                embedding: Optional[bool] = True, priority: int = 0,
                tags: Optional[str] = None, emotion: Optional[str] = None,
                persona_context: Optional[str] = None):
    """Simpan pelajaran baru ke database Bob"""
    embedding_vector = None
    if embedding:
        try:
            embedding_vector = pickle.dumps(get_embedding(isi))
        except Exception as e:
            print(f"[Embedding Error] {e}")

    memory = Memory(
        phone=phone,
        kode_satker=kode_satker,
        topik=topik,
        isi=isi,
        priority=priority,
        embedding=embedding_vector,
        tags=persona_context or tags,
        emotion=emotion,
        created_at=datetime.now(timezone.utc)
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory

def get_memories_by_phone(db: Session, phone: str, persona_context: Optional[str] = None):
    """Ambil semua memori berdasarkan nomor pengguna"""
    if not phone:
        return []
    return db.query(Memory).filter(Memory.phone == phone).order_by(Memory.created_at.desc()).all()

def summarize_by_topik(db: Session, kode_satker: str = None):
    """Ambil ringkasan jumlah memori per topik"""
    query = db.query(Memory.topik)
    if kode_satker:
        query = query.filter(Memory.kode_satker == kode_satker)
    topik_rows = query.all()
    if not topik_rows:
        return {}
    topik_list = [row[0] for row in topik_rows if row[0]]
    result = {}
    for topik in topik_list:
        result[topik] = result.get(topik, 0) + 1
    return result


# Fungsi untuk menyimpan hubungan antar memori ke tabel MemoryLink
from models import MemoryLink

def link_memories(db: Session, from_id: int, to_id: int, relation_type: str = "menguatkan", weight: int = 1):
    """Simpan hubungan antar memori ke database"""
    if not from_id or not to_id or from_id == to_id:
        return None
    link = MemoryLink(
        from_id=from_id,
        to_id=to_id,
        relation_type=relation_type,
        weight=weight
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def get_linked_memories(db: Session, memory_id: int):
    """
    Ambil semua memori yang terhubung dengan memory_id tertentu berdasarkan relasi dari tabel MemoryLink.
    Mengembalikan list Memory yang menjadi target dari memory_id (sebagai from_id).
    Aman jika tidak ada data relasi, akan mengembalikan list kosong.
    """
    links = db.query(MemoryLink).filter(MemoryLink.from_id == memory_id).all()
    if not links:
        return []
    linked_ids = [link.to_id for link in links]
    return db.query(Memory).filter(Memory.id.in_(linked_ids)).all()


# Fungsi auto_link_memory: otomatis membuat relasi antar memori yang relevan secara semantik
def auto_link_memory(db: Session, phone: str, kode_satker: str, threshold: float = 0.75):
    """
    Membandingkan memori terakhir user dengan semua memori sebelumnya.
    Jika similarity tinggi, akan disimpan sebagai MemoryLink.
    """
    memories = get_memories_by_phone(db, phone)
    if len(memories) < 2:
        return

    latest = memories[0]
    if not latest.embedding:
        return

    try:
        latest_vec = pickle.loads(latest.embedding)
        if not isinstance(latest_vec, np.ndarray):
            return
    except Exception as e:
        print(f"[AutoLink Error] Gagal parse embedding: {e}")
        return

    for prev in memories[1:]:
        if not prev.embedding:
            continue
        try:
            prev_vec = pickle.loads(prev.embedding)
            if not isinstance(prev_vec, np.ndarray):
                continue
            sim = cosine_similarity([latest_vec], [prev_vec])[0][0]
            if sim >= threshold:
                link_memories(db, from_id=latest.id, to_id=prev.id, relation_type="semantic", weight=int(sim * 100))
                print(f"[🔗 Link] Memory {latest.id} ↔ {prev.id} (sim: {sim:.2f})")
        except Exception as e:
            print(f"[AutoLink Error] {e}")
            continue