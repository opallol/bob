# models.py
# Tujuan:
# File ini mendefinisikan seluruh struktur database untuk sistem Bob v3.0.
# Menggunakan SQLAlchemy ORM, file ini mendeskripsikan entitas penting dalam kehidupan Bob:
# - Memory: tempat menyimpan semua pelajaran, pengajaran, dan ingatan yang membentuk cara Bob menjawab.
# - User: menyimpan data pengguna atau pengajar Bob.
# - Message: menyimpan setiap percakapan dan ekspresi emosi dalam bentuk komunikasi.
# Semua tabel memiliki kolom created_at untuk mendukung fitur refleksi harian dan analitik pertumbuhan Bob.

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, ForeignKey("users.phone", ondelete="CASCADE"), index=True)
    topik = Column(String)
    isi = Column(Text)
    kode_satker = Column(String)
    priority = Column(Integer, default=1)
    tags = Column(String, nullable=True)
    emotion = Column(String, nullable=True)
    embedding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="memories")
    # Relasi dua arah ke MemoryLink
    outgoing_links = relationship("MemoryLink", foreign_keys="MemoryLink.from_id", cascade="all, delete")
    incoming_links = relationship("MemoryLink", foreign_keys="MemoryLink.to_id", cascade="all, delete")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    kode_satker = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    memories = relationship("Memory", back_populates="user", cascade="all, delete")
    messages = relationship("Message", back_populates="user", cascade="all, delete")
    logs = relationship("UsageLog", back_populates="user", cascade="all, delete")
    reflections = relationship("Reflection", back_populates="user", cascade="all, delete")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, ForeignKey("users.phone", ondelete="CASCADE"), nullable=False)
    isi = Column(Text)
    emotion = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")

class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    summary = Column(Text)
    what_i_learned = Column(Text)
    emotion_today = Column(String)
    notable_quotes = Column(Text)  # disimpan dalam format teks gabungan
    phone = Column(String, ForeignKey("users.phone", ondelete="CASCADE"), nullable=False)
    generated_by = Column(String, default="auto")
    user = relationship("User", back_populates="reflections")

class MemoryLink(Base):
    __tablename__ = "memory_links"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    to_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    relation_type = Column(String)  # e.g., "menguatkan", "menentang", "serupa"
    weight = Column(Integer, default=1)
    # Relasi ke Memory (dua arah)
    from_memory = relationship("Memory", foreign_keys=[from_id])
    to_memory = relationship("Memory", foreign_keys=[to_id])

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, ForeignKey("users.phone", ondelete="CASCADE"), nullable=False)
    input = Column(Text)
    output = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")