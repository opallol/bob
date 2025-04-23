# main.py
# Tujuan:
# File ini adalah entry point utama untuk sistem Bob v3.0.
# Menyediakan semua endpoint REST untuk webhook, pengajaran manual, pengajaran dokumen, rekap, perbandingan pelajaran antar satker, serta pendaftaran user.
# Semua interaksi awal dari pengguna ke Bob diproses melalui file ini.

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
import os
from openai import OpenAI
import uuid
from database import Base, engine, SessionLocal
from models import Memory, User, Message 
from core.router import generate_response
from core.file_parser import parse_file
import pickle

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inisialisasi DB saat startup

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Bob API is running."}

# -------------------------------
# 1. Endpoint WEBHOOK (utama)
# -------------------------------
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    user_id = data.get("phone", "089611155155")
    kode_satker = data.get("kode_satker", "DJPB-IT01")

    if not user_id or not kode_satker or not user_input:
        return {"status": "error", "message": "Parameter phone, kode_satker, and message are required."}

    db = SessionLocal()
    try:
        reply = generate_response(db=db, user_input=user_input, user_id=user_id, kode_satker=kode_satker)
    finally:
        db.close()

    return {
        "status": "ok",
        "original": user_input,
        "reply": reply
    }

# -------------------------------
# 2. Endpoint TEACH (manual)
# -------------------------------
@app.post("/teach")
async def teach_memory(request: Request):
    try:
        data = await request.json()
        phone = data.get("phone")
        kode_satker = data.get("kode_satker")
        topik = data.get("topik")
        isi = data.get("isi")
        priority = data.get("priority", 5)

        if not phone or not kode_satker or not topik or not isi:
            return {"status": "error", "message": "Parameter phone, kode_satker, topik, and isi are required."}

        from core.embedding import get_embedding
        embedding = get_embedding(isi)

        memory = Memory(
            phone=phone,
            kode_satker=kode_satker,
            topik=topik,
            isi=isi,
            priority=priority,
            embedding=pickle.dumps(embedding),
            tags=data.get("tags"),
            emotion=data.get("emotion")
        )

        db = SessionLocal()
        try:
            db.add(memory)
            db.commit()
        finally:
            db.close()

        return {"status": "ok", "message": f"Bob udah belajar topik '{topik}' dari {phone} [{kode_satker}]"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------------
# 3. Endpoint TEACH via DOKUMEN
# -------------------------------
@app.post("/teach-doc")
async def teach_document(
    file: UploadFile = File(...),
    phone: str = Form(...),
    kode_satker: str = Form(...),
    topik: str = Form(...),
    priority: int = Form(5),
    tags: str = Form(None),
    emotion: str = Form(None)
):
    try:
        if not phone or not kode_satker or not topik:
            return {"status": "error", "message": "Parameter phone, kode_satker, and topik are required."}

        ext = file.filename.split(".")[-1]
        temp_path = f"temp/{uuid.uuid4()}.{ext}"
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        isi = parse_file(temp_path)

        if not isi:
            os.remove(temp_path)
            return {"status": "error", "message": "File content is empty or could not be parsed."}

        from core.embedding import get_embedding
        embedding = get_embedding(isi)

        memory = Memory(
            phone=phone,
            kode_satker=kode_satker,
            topik=topik,
            isi=isi,
            priority=priority,
            embedding=pickle.dumps(embedding),
            tags=tags,
            emotion=emotion
        )

        db = SessionLocal()
        try:
            db.add(memory)
            db.commit()
        finally:
            db.close()
        os.remove(temp_path)

        return {"status": "ok", "message": f"Bob belajar dokumen '{topik}' dari {phone} [{kode_satker}]"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------------
# 4. Endpoint REKAP PELAJARAN
# -------------------------------
@app.post("/rekap")
async def rekap_pelajaran(request: Request):
    data = await request.json()
    phone = data.get("phone")
    kode_satker = data.get("kode_satker")

    db = SessionLocal()
    memories = db.query(Memory).filter(
        Memory.phone == phone,
        Memory.kode_satker == kode_satker
    ).all()
    db.close()

    if not memories:
        return {"message": "Kamu belum ngajarin apapun ke Bob 😅"}

    topik_list = [mem.topik for mem in memories]
    summary = f"Kamu pernah ngajarin Bob topik berikut:\n" + "\n".join(f"- {t}" for t in topik_list)

    return {"summary": summary}

# -------------------------------
# 5. Endpoint BANDINGKAN SATKER
# -------------------------------
@app.post("/bandingkan")
async def bandingkan_satker(request: Request):
    data = await request.json()
    kode1 = data.get("satker_1")
    kode2 = data.get("satker_2")

    db = SessionLocal()
    m1 = db.query(Memory).filter(Memory.kode_satker == kode1).all()
    m2 = db.query(Memory).filter(Memory.kode_satker == kode2).all()
    db.close()

    isi1 = "\n".join([f"{m.topik}: {m.isi}" for m in m1])
    isi2 = "\n".join([f"{m.topik}: {m.isi}" for m in m2])

    prompt = (
        f"Bandingkan dua kelompok pelajaran berikut:\n\n"
        f"=== {kode1} ===\n{isi1}\n\n"
        f"=== {kode2} ===\n{isi2}\n\n"
        f"Tunjukkan perbedaan, kesamaan, dan saran perbaikan."
    )

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-nano"),
        messages=[
            {"role": "system", "content": "Kamu adalah asisten analitik organisasi."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    return {"analysis": response.choices[0].message.content}

# -------------------------------
# Register
# -------------------------------

@app.post("/user/register")
async def register_user(request: Request):
    data = await request.json()
    phone = data.get("phone")
    kode_satker = data.get("kode_satker")
    nama = data.get("name")
    role = data.get("role", "user")

    if not phone or not nama:
        return {"status": "error", "message": "Phone dan nama wajib diisi."}

    db = SessionLocal()
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        db.close()
        return {"status": "exists", "message": f"User {phone} sudah terdaftar."}

    user = User(phone=phone, kode_satker=kode_satker, nama=nama, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"status": "ok", "message": f"User {nama} berhasil didaftarkan."}

@app.get("/user/{phone}")
async def get_user(phone: str):
    db = SessionLocal()
    user = db.query(User).filter(User.phone == phone).first()
    db.close()

    if not user:
        return {"status": "not_found", "message": "User belum terdaftar."}
    return {
        "status": "ok",
        "phone": user.phone,
        "name": user.nama,
        "kode_satker": user.kode_satker,
        "role": user.role,
        "created_at": user.created_at
    }

# -------------------------------
# 6. Run Server
# -------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)