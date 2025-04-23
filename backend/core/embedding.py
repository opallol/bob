# embedding.py
# Tujuan:
# Modul ini menangani pembuatan embedding vector dari input teks untuk sistem memori Bob.
# Prioritas utama adalah OpenAI API (text-embedding-ada-002),
# dengan fallback otomatis ke model lokal ('all-MiniLM-L6-v2') jika API gagal diakses.
# Ini memungkinkan Bob tetap dapat berfungsi meski offline atau tanpa API aktif.

import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import logging

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
local_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> np.ndarray:
    """
    Ambil embedding vector dari teks.
    Prioritas ke OpenAI untuk kualitas embedding optimal.
    Jika gagal, fallback ke SentenceTransformer lokal.
    """
    text = text.replace("\n", " ")
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        logger.warning(f"[Embedding Fallback] OpenAI failed, using local model. Error: {e}")
        return local_model.encode(text, convert_to_numpy=True)