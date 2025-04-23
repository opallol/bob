# file_parser.py
# Tujuan:
# File ini menangani ekstraksi teks dari berbagai jenis file dokumen
# yang dapat digunakan Bob untuk proses pembelajaran dan penyimpanan ingatan.
# Format yang didukung: .pdf, .docx, .txt, dan .md.
# Semua fungsi mengembalikan string teks bersih yang bisa langsung disimpan ke memori Bob.

import fitz  # PyMuPDF
import docx
import os

def parse_pdf(file_path):
    """Ekstrak teks dari file PDF"""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

def parse_docx(file_path):
    """Ekstrak teks dari file DOCX"""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs]).strip()

def parse_txt(file_path):
    """Baca file .txt biasa"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def parse_md(file_path):
    """Baca file .md (Markdown) biasa"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def parse_file(file_path):
    """Deteksi ekstensi & panggil parser yang sesuai"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")
    try:
        if file_path.endswith(".pdf"):
            return parse_pdf(file_path)
        elif file_path.endswith(".docx"):
            return parse_docx(file_path)
        elif file_path.endswith(".txt"):
            return parse_txt(file_path)
        elif file_path.endswith(".md"):
            return parse_md(file_path)
        else:
            raise ValueError("Format file tidak didukung. Gunakan .pdf, .docx, .txt, atau .md.")
    except Exception as e:
        raise RuntimeError(f"Gagal memproses file: {e}")