

from models import Memory
from sqlalchemy.orm import Session
from collections import Counter
from datetime import datetime, timedelta

def get_top_topics(db: Session, limit=5):
    """Ambil topik paling sering muncul dari memori Bob"""
    topik_list = db.query(Memory.topik).all()
    counter = Counter(t[0] for t in topik_list if t[0])
    return counter.most_common(limit)

def get_top_emotions(db: Session, limit=5):
    """Ambil emosi yang paling sering tercatat"""
    emotion_list = db.query(Memory.emotion).all()
    counter = Counter(e[0] for e in emotion_list if e[0])
    return counter.most_common(limit)

def get_recent_insight(db: Session, days=7):
    """Ambil insight interaksi dan emosi dalam 7 hari terakhir"""
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    recent = db.query(Memory).filter(Memory.created_at >= cutoff).all()
    
    topik_counter = Counter(m.topik for m in recent if m.topik)
    emotion_counter = Counter(m.emotion for m in recent if m.emotion)

    return {
        "total_memories": len(recent),
        "top_topics": topik_counter.most_common(3),
        "top_emotions": emotion_counter.most_common(3),
        "period_start": cutoff.isoformat(),
        "period_end": now.isoformat()
    }