"""SQLite 持久化（SQLAlchemy）。"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "designs.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()

class 設計記錄(Base):
    __tablename__ = "designs"
    id = Column(Integer, primary_key=True)
    名稱 = Column(String(100))
    功能 = Column(String(50))
    參數 = Column(Text)
    建立時間 = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def 新增記錄(名稱, 功能, 參數):
    s = Session()
    s.add(設計記錄(名稱=名稱, 功能=功能, 參數=參數))
    s.commit()
    s.close()

def 列出記錄():
    s = Session()
    rows = s.query(設計記錄).all()
    s.close()
    return rows
