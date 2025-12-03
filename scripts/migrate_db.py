#!/usr/bin/env python
"""
Script para migrar la base de datos y añadir las nuevas columnas necesarias.
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db import engine, Base, Invoice, User
from sqlalchemy import text

def migrate():
    """Migra la base de datos añadiendo las nuevas columnas"""
    print("🔧 Iniciando migración de base de datos...")
    
    # Crear todas las tablas nuevas (por si no existen)
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas base creadas/verificadas")
    
    # Conectar a la BD y añadir columnas si no existen
    with engine.connect() as conn:
        # Verificar qué columnas existen
        result = conn.execute(text("PRAGMA table_info(invoices)"))
        existing_columns = [row[1] for row in result]
        
        print(f"Columnas existentes: {existing_columns}")
        
        # Añadir columnas faltantes
        if 'user_id' not in existing_columns:
            print("➕ Añadiendo columna user_id...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN user_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id)"))
            print("✓ Columna user_id añadida")
        
        if 'data_complete' not in existing_columns:
            print("➕ Añadiendo columna data_complete...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN data_complete TEXT"))
            print("✓ Columna data_complete añadida")
        
        if 'raw_text_ocr' not in existing_columns:
            print("➕ Añadiendo columna raw_text_ocr...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN raw_text_ocr TEXT"))
            print("✓ Columna raw_text_ocr añadida")
        
        if 'created_at' not in existing_columns:
            print("➕ Añadiendo columna created_at...")
            conn.execute(text("ALTER TABLE invoices ADD COLUMN created_at DATETIME"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at)"))
            print("✓ Columna created_at añadida")
        
        conn.commit()
    
    print("\n✅ Migración completada exitosamente")
    print("La base de datos ahora tiene todas las columnas necesarias.")

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        sys.exit(1)

