from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from pdf2image import convert_from_path
import os
import tempfile

def images_from_file(path):
    """
    Convierte un archivo (PDF o imagen) a lista de imágenes PIL
    """
    ext = os.path.splitext(path)[1].lower()
    
    # Intentar detectar si es PDF
    is_pdf = False
    
    # Método 1: Por extensión
    if ext in ('.pdf',):
        is_pdf = True
    
    # Método 2: Leer primeros bytes (más robusto)
    if not is_pdf:
        try:
            with open(path, 'rb') as f:
                header = f.read(5)
                if header.startswith(b'%PDF'):
                    is_pdf = True
        except:
            pass
    
    # Procesar según tipo
    if is_pdf:
        try:
            # Intentar encontrar poppler automáticamente
            poppler_path = None
            
            # Rutas comunes de poppler en Windows
            possible_paths = [
                r"C:\Program Files\poppler\Library\bin",
                r"C:\Program Files (x86)\poppler\Library\bin",
                r"C:\poppler\Library\bin",
                r"C:\Program Files\poppler-23.11.0\Library\bin",
                r"C:\Program Files\poppler-24.08.0\Library\bin",
                r"C:\Users\User\Downloads\poppler-25.11.0\Library\bin",
                # Agregar más rutas si es necesario
            ]
            
            for p in possible_paths:
                if os.path.exists(p):
                    poppler_path = p
                    break
            
            # Convertir PDF a imágenes (requiere poppler)
            if poppler_path:
                images = convert_from_path(path, poppler_path=poppler_path)
            else:
                # Intentar sin especificar ruta (por si está en PATH)
                images = convert_from_path(path)
            
            return images
        except Exception as e:
            print(f"Error al convertir PDF: {e}")
            raise Exception(f"No se pudo procesar el PDF. ¿Está poppler instalado? Error: {e}")
    else:
        # Intentar abrir como imagen
        try:
            return [Image.open(path)]
        except Exception as e:
            raise Exception(f"No se pudo abrir el archivo como imagen o PDF. Error: {e}")

def ocr_image(pil_image, lang='spa+eng'):
    """
    Extrae texto de una imagen PIL usando Tesseract
    """
    try:
        text = pytesseract.image_to_string(pil_image, lang=lang)
        return text
    except Exception as e:
        raise Exception(f"Error en OCR. ¿Está Tesseract instalado? Error: {e}")

def ocr_file(path):
    """
    Extrae texto de un archivo (PDF o imagen)
    """
    try:
        images = images_from_file(path)
        texts = [ocr_image(img) for img in images]
        return "\n\n".join(texts)
    except Exception as e:
        raise Exception(f"Error procesando archivo: {e}")