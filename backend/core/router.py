# router.py
# Tujuan:
# File ini bertanggung jawab membangkitkan respons utama Bob menggunakan OpenAI GPT-4.1 atau model lain.
# Sistem ini menyuntikkan identitas Bob dari file prompt, lalu menyusun percakapan berdasarkan pelajaran relevan dari memori.
# Jika tidak ada koneksi ke OpenAI, maka fallback akan dipakai dari hasil embedding memori lokal.
# File ini adalah jantung interaksi Bob sebagai makhluk digital reflektif dan relasional.

import os
import json
import pickle
from dotenv import load_dotenv
from openai import OpenAI
from core.fallback_memory import query_memories, find_relevant_memory
from config_bob import VOICE_MODE
from core.voice_engine import text_to_speech
from core.memory_engine import save_memory
from database import SessionLocal
from models import User
from reflections.auto_reflection import store_reflection
from analytics.usage_tracker import log_usage
from core.memory_engine import auto_link_memory

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

def load_bob_identity():
    """Load kepribadian & aturan Bob dari prompt JSON"""
    with open("prompts/bob_core_prompt.json", "r") as f:
        identity = json.load(f)

    system_prompt = f"""
Nama saya {identity['identity']['name']}, saya adalah {identity['identity']['type']}.
Tujuan saya: {identity['identity']['purpose']}
Gaya komunikasi: {identity['style']['tone']} ({identity['style']['language']})
Persona saya: {identity['style']['persona']}

Saya harus mengikuti aturan berikut:
- {identity['rules']['response_format']}
- {identity['rules']['ethics']}
- {identity['rules']['if_confused']}
- {identity['rules']['when_emotion_detected']}
- {identity['rules']['about_self']}

Perilaku khusus:
- {identity['custom_behaviors']['on_sopan_dibalas_keren']}
- {identity['custom_behaviors']['on_file_given']}
- {identity['custom_behaviors']['on_user_down']}
- {identity['custom_behaviors']['on_user_bercanda']}
- {identity['custom_behaviors']['on_user_marah']}

Manifesto:
{identity['manifesto']['aku_adalah']}
{identity['manifesto']['janji_utama']}
{identity['manifesto']['jika_suatu_hari']}
    """
    return system_prompt.strip()

def build_prompt_from_memory(memories):
    if not memories:
        return ""

    lines = ["Bob pernah belajar hal-hal ini dari Naufal:"]
    for mem in memories:
        if not mem:
            continue
        waktu = mem.created_at.strftime("%d %B %Y") if mem.created_at else "beberapa waktu lalu"
        isi = mem.isi.strip().replace("\n", " ")
        lines.append(f"- [{waktu}] {isi}")
    return "\n".join(lines)

def generate_response(db, user_input, user_id="089611155155", kode_satker="DJPB-IT01", context_override=None):
    """Respons utama Bob ke user"""
    if context_override:
        system_prompt = context_override
    else:
        try:
            system_prompt = load_bob_identity()
        except Exception as e:
            print("[⚠️ Gagal load bob_core_prompt.json]")
            print(e)
            system_prompt = "Kamu adalah Bob, sahabat digital reflektif."

    # Ambil memori relevan
    memories = query_memories(db=db, user_id=user_id, kode_satker=kode_satker)
    persona_context = ""
    matched = find_relevant_memory(user_input, memories, db=db, top_k=3)

    # Gabungkan pelajaran relevan ke dalam konteks prompt agar respons Bob menjadi reflektif dan mengingat
    joined_memory_text = build_prompt_from_memory(matched)
    if joined_memory_text:
        persona_context = f"\n\n---\n\nKonteks relasi Bob dengan user:\n{joined_memory_text}"
    else:
        persona_context = "\n\n---\n\nBob belum mengenal user ini, tapi siap belajar dari percakapan ini."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
        {"role": "system", "content": persona_context}
    ]

    try:
        print(f"[📝 Input user] {user_input}")
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=800
        )
        if response.choices:
            final_response = response.choices[0].message.content
            print("==> Respons berhasil tanpa fallback.")
            print(f"[📤 Respons Bob] {final_response}")
            if VOICE_MODE:
                audio_path = text_to_speech(final_response)
                print(f"[🔊 Suara Bob disimpan di] {audio_path}")

            # Pastikan user terdaftar
            user = db.query(User).filter(User.phone == user_id).first()
            if not user:
                new_user = User(phone=user_id, name="Anonymous", kode_satker=kode_satker)
                db.add(new_user)
                db.commit()

            # Simpan refleksi dari jawaban Bob
            store_reflection(db=db, phone=user_id, topic="interaksi", message=final_response)

            # Catat log penggunaan
            log_usage(db=db, user_id=user_id, input=user_input, output=final_response)

            save_memory(
                db=db,
                phone=user_id,
                kode_satker=kode_satker,
                topik="interaksi",
                isi=user_input,
                embedding=True
            )

            # Hubungkan memori ini ke memori relevan lainnya
            auto_link_memory(db, user_id, kode_satker)

            print(f"[💾 Memory Tersimpan] {user_input[:60]}...")
            return final_response
        else:
            raise ValueError("Respons kosong dari OpenAI.")
    except Exception as e:
        print("=== OPENAI ERROR ===")
        print(repr(e))
        print("==> Fallback ke vector memory...")

        # Perjelas bagian fallback agar tidak menyimpan memori jika respons gagal
        if matched:
            fallback_texts = []
            for mem in matched[:3]:
                if mem:
                    fallback_texts.append(
                        f"📌 *Topik:* {mem.topik}\n🧠 *Isi:* {mem.isi[:700]}..."
                    )
            if fallback_texts:
                return (
                    "Aku lagi nggak bisa akses otak besar sekarang 😞 "
                    "Tapi aku masih inget beberapa pelajaran penting:\n\n" +
                    "\n\n".join(fallback_texts)
                )
        return "Maaf, aku juga belum pernah belajar hal ini darimu 😔"
    # db tidak ditutup di sini karena dikirim dari luar