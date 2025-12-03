from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/invoices.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Campos básicos (mantenemos para compatibilidad y búsquedas rápidas)
    invoice_number = Column(String, index=True)
    supplier = Column(String)
    nit = Column(String)
    date = Column(String)
    subtotal = Column(String)
    tax = Column(String)
    total = Column(String)
    # Almacenar TODA la información extraída por el modelo como JSON
    data_complete = Column(Text)  # JSON completo con todos los campos
    raw_text_ocr = Column(Text)  # Texto OCR completo
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relación con usuario
    user = relationship("User", backref="invoices")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)
