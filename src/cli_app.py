import argparse
from ocr_utils import ocr_file
import json

def extract_basic_fields(text):
    # placeholder simple: buscar lineas con "Factura", "Fecha", etc.
    lines = text.splitlines()
    result = {"raw_text": text}
    # TODO: reemplazar por NLP/regex robusto
    for ln in lines:
        if 'Factura' in ln or 'FACTURA' in ln:
            result.setdefault('candidates', []).append(ln.strip())
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Intelli-Invoice Extractor CLI")
    parser.add_argument('file', help="ruta a PDF o imagen")
    args = parser.parse_args()
    text = ocr_file(args.file)
    parsed = extract_basic_fields(text)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
