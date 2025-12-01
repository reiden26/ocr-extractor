#!/usr/bin/env python
"""
Script para verificar que todo el entorno está correctamente configurado
"""
import sys
import os

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Versión correcta")
        return True
    else:
        print("   ❌ Se requiere Python 3.8+")
        return False

def check_tesseract():
    """Verifica que Tesseract está instalado"""
    try:
        import pytesseract
        from PIL import Image
        print("📝 Tesseract OCR")
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   ✅ Instalado: v{version}")
            return True
        except:
            print("   ❌ Tesseract no encontrado en PATH")
            return False
    except ImportError:
        print("📝 Tesseract OCR")
        print("   ❌ pytesseract no instalado")
        return False

def check_packages():
    """Verifica paquetes Python requeridos"""
    packages = [
        ('PIL', 'Pillow'),
        ('pdf2image', 'pdf2image'),
        ('pandas', 'Pandas'),
        ('spacy', 'spaCy'),
        ('sklearn', 'scikit-learn'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('streamlit', 'Streamlit'),
    ]
    
    all_ok = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"📦 {name}: ✅")
        except ImportError:
            print(f"📦 {name}: ❌ No instalado")
            all_ok = False
    
    return all_ok

def check_spacy_model():
    """Verifica el modelo de spaCy"""
    try:
        import spacy
        print("🧠 Modelo spaCy")
        try:
            nlp = spacy.load("es_core_news_sm")
            print("   ✅ es_core_news_sm instalado")
            return True
        except:
            print("   ⚠️  es_core_news_sm no encontrado")
            print("   Ejecuta: python -m spacy download es_core_news_sm")
            return False
    except ImportError:
        print("🧠 Modelo spaCy: ❌ spaCy no instalado")
        return False

def check_directories():
    """Verifica directorios necesarios"""
    dirs = ['data', 'scripts', 'src']
    all_ok = True
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"📁 {dir_name}/: ✅")
        else:
            print(f"📁 {dir_name}/: ❌ No existe")
            all_ok = False
    return all_ok

def check_database():
    """Verifica la base de datos"""
    db_path = 'data/invoices.db'
    if os.path.exists(db_path):
        print(f"💾 Base de datos: ✅ ({db_path})")
        
        # Verificar que se puede conectar
        try:
            sys.path.insert(0, 'src')
            from db import SessionLocal
            db = SessionLocal()
            db.close()
            print("   ✅ Conexión exitosa")
            return True
        except Exception as e:
            print(f"   ⚠️  Error al conectar: {e}")
            return False
    else:
        print(f"💾 Base de datos: ⚠️  No creada")
        print("   Ejecuta: python scripts/init_db.py")
        return False

def main():
    print("=" * 60)
    print("🔍 VERIFICACIÓN DEL ENTORNO - Intelli-Invoice Extractor")
    print("=" * 60)
    print()
    
    checks = [
        ("Python", check_python_version()),
        ("Tesseract", check_tesseract()),
        ("Paquetes", check_packages()),
        ("Modelo spaCy", check_spacy_model()),
        ("Directorios", check_directories()),
        ("Base de datos", check_database()),
    ]
    
    print()
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    for name, status in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print()
    if passed == total:
        print("🎉 ¡Todo está configurado correctamente!")
        print("Puedes ejecutar: streamlit run src/app.py")
    else:
        print(f"⚠️  {total - passed} problema(s) encontrado(s)")
        print("Revisa los mensajes anteriores y la guía de instalación")
    
    print("=" * 60)
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)