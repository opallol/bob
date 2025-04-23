# database.py
# Tujuan:
# File ini adalah pusat inisialisasi koneksi database untuk sistem Bob.
# Secara default menggunakan SQLite, namun bisa diubah ke PostgreSQL atau database lain melalui konfigurasi .env (DATABASE_URL).
# Semua session database dan ORM berasal dari sini.

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "bob.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Coba tes koneksi saat startup
try:
    with engine.connect() as connection:
        print(f"[DB] Koneksi database berhasil. Path: {db_path}")
except Exception as e:
    print(f"[WARNING] Gagal konek ke database: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()