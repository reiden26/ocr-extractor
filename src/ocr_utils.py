from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os
import tempfile

def images_from_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.pdf',):
        # convierte pdf a lista de PIL images (requiere poppler)
        images = convert_from_path(path)
        return images
    else:
        return [Image.open(path)]

def ocr_image(pil_image, lang='spa+eng'):
    # devuelve texto crudo
    text = pytesseract.image_to_string(pil_image, lang=lang)
    return text

def ocr_file(path):
    images = images_from_file(path)
    texts = [ocr_image(img) for img in images]
    return "\n\n".join(texts)
