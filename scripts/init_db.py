#!/usr/bin/env python
"""
Script para inicializar la base de datos SQLite
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db import init_db, engine, Invoice
from sqlalchemy import inspect

def main():
    print("🔧 Inicializando base de datos SQLite...")
    
    # Crear directorio data si no existe
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    print(f"✓ Directorio data: {data_dir}")
    
    # Crear tablas
    init_db()
    print("✓ Tablas creadas")
    
    # Verificar tablas
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✓ Tablas en BD: {', '.join(tables)}")
    
    # Mostrar esquema de la tabla invoices
    if 'invoices' in tables:
        columns = inspector.get_columns('invoices')
        print("\n📋 Esquema de tabla 'invoices':")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    
    print("\n✅ Base de datos lista para usar")
    print(f"📍 Ubicación: data/invoices.db")

if __name__ == '__main__':
    main()