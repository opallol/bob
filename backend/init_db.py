# init_db.py
# Tujuan:
# Inisialisasi database Bob: membuat file bob.db dan seluruh tabel ORM.

from database import engine
from models import Base

# Debug echo untuk menampilkan SQL saat dijalankan (opsional)
engine.echo = True

print("⏳ Membuat file dan seluruh struktur tabel database Bob...")

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Struktur database Bob berhasil dibuat (users, memories, memory_links, reflections, usage_logs).")
except Exception as e:
    print("❌ Gagal membuat struktur database.")
    print(f"Error: {e}")
