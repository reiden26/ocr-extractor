from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/invoices.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, index=True)
    supplier = Column(String)
    nit = Column(String)
    date = Column(String)
    subtotal = Column(String)
    tax = Column(String)
    total = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)
