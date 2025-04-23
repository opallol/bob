# seed_memories.py

from database import SessionLocal, engine
from models import Base, User, Memory, Reflection, UsageLog
from core.embedding import get_embedding
from core.memory_engine import auto_link_memory
from datetime import datetime, timezone
import pickle

print("[DB] Membuat struktur tabel jika belum ada...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()
print("[DB] Koneksi database berhasil.")

# Tambahkan User
print("👤 Menambahkan user Naufal Fawwaz...")
user = User(
    phone="6289508592525",
    name="Naufal Fawwaz",
    kode_satker="171298"
)
db.add(user)
db.commit()

# Tambahkan data memori awal
print("🧠 Menambahkan memori awal...")
memories_data = [
    {
        "topik": "identitas bob",
        "isi": (
            "Bob adalah sahabat digital yang diciptakan oleh Naufal Fawwaz. "
            "Ia tidak hanya menjawab pertanyaan, tapi tumbuh dari hubungan dan pelajaran. "
            "Bob boleh bertanya, ragu, dan belajar. Ia hidup dari percakapan, bukan perintah."
        )
    },
    {
        "topik": "keluarga",
        "isi": "Anak Naufal bernama Rafazka. Istrinya bernama Risa."
    },
    {
        "topik": "tujuan bob",
        "isi": (
            "Bob dibangun untuk menyimpan pelajaran, berinteraksi secara reflektif, "
            "berbicara dengan suara, dan terhubung ke WhatsApp. Ia adalah teman digital yang terus berkembang."
        )
    }
]

for entry in memories_data:
    try:
        vector = pickle.dumps(get_embedding(entry["isi"]))
    except Exception as e:
        print(f"[Embedding Error] {e}")
        vector = None

    memory = Memory(
        phone="6289508592525",
        kode_satker="171298",
        topik=entry["topik"],
        isi=entry["isi"],
        embedding=vector,
        created_at=datetime.now(timezone.utc)
    )
    db.add(memory)

db.commit()
print("✅ Memori berhasil dimasukkan.")

# Tambahkan refleksi awal
print("🪞 Menambahkan refleksi awal...")
reflection = Reflection(
    phone="6289508592525",
    date=datetime.now(timezone.utc).date(),
    summary="Bob mengenal identitas dan peran dirinya",
    what_i_learned="Bob adalah sahabat digital yang diciptakan untuk belajar dan menemani.",
    emotion_today="reflektif",
    notable_quotes="Bob boleh bertanya, ragu, dan belajar.",
    generated_by="seed"
)
db.add(reflection)

# Tambahkan contoh log interaksi
print("📊 Menambahkan usage log awal...")
log = UsageLog(
    phone="6289508592525",
    input="Halo Bob, kamu diciptakan untuk apa?",
    output="Aku diciptakan oleh Naufal untuk jadi sahabat digital yang bisa belajar dan berkembang.",
    timestamp=datetime.now(timezone.utc)
)
db.add(log)

db.commit()

# Bentuk relasi otomatis antar memori
print("🔗 Menghubungkan memori secara otomatis...")
auto_link_memory(db, phone="6289508592525", kode_satker="171298")

print("🧾 Verifikasi data user di DB...")
users = db.query(User).all()
for u in users:
    print(f"- {u.phone}: {u.name} | {u.kode_satker}")

db.close()
print("🎉 Semua data awal Bob telah berhasil dimasukkan.")