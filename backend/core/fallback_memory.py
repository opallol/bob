# fallback_memory.py
# Tujuan:
# File ini berisi fungsi-fungsi untuk mengambil dan mencari ingatan Bob yang paling relevan
# berdasarkan user_input dan memori yang tersimpan dalam database.
# Cocok untuk fallback saat GPT butuh konteks dari pengalaman sebelumnya.
# Menggunakan vektor embedding + cosine similarity.

import logging
from database import SessionLocal
from models import Memory
import pickle
import numpy as np
from core.embedding import get_embedding

def query_memories(db, user_phone, kode_satker):
    """Ambil semua memory berdasarkan db, user, dan satker"""
    memories = db.query(Memory)\
        .filter(Memory.phone == user_phone)\
        .filter(Memory.kode_satker == kode_satker)\
        .all()
    return memories

def find_relevant_memory(user_input, memories, top_k=3):
    """
    Cari beberapa memory paling relevan secara semantik.
    Mengembalikan daftar top_k memory dengan skor similarity tertinggi.

    Args:
        user_input (str): Input dari user.
        memories (list): Daftar memory yang akan dicari.
        top_k (int, optional): Jumlah memory teratas yang dikembalikan. Default: 3.
    Returns:
        list: Daftar memory paling relevan (maksimal top_k).
    """
    user_vector = get_embedding(user_input)
    scored_memories = []

    for mem in memories:
        # Validasi tipe embedding harus bytes/bytearray
        if not isinstance(mem.embedding, (bytes, bytearray)):
            continue
        try:
            memory_vector = pickle.loads(mem.embedding)
            if not isinstance(memory_vector, np.ndarray):
                continue
            similarity = cosine_similarity(user_vector, memory_vector)
            logging.debug(f"[Memory Match] Similarity: {similarity:.3f} | Topik: {mem.topik}")
            scored_memories.append((similarity, mem))
        except Exception as e:
            logging.warning(f"[Fallback Memory] Error parsing embedding: {e}")
            continue

    scored_memories.sort(reverse=True, key=lambda x: x[0])

    if not scored_memories:
        logging.info("[Memory Match] Tidak ditemukan memori relevan.")

    return [mem for _, mem in scored_memories[:top_k]]

def cosine_similarity(vec1, vec2):
    """Hitung kesamaan kosinus antar 2 vektor"""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)