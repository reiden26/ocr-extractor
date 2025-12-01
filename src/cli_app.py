import argparse
from ocr_utils import ocr_file
from extractor import extract_invoice_data
from db import SessionLocal, Invoice, init_db
import json
import sys

def save_to_db(data):
    """Guarda los datos extraídos en la base de datos"""
    try:
        db = SessionLocal()
        invoice = Invoice(
            invoice_number=data.get('invoice_number'),
            supplier=data.get('supplier'),
            nit=data.get('nit'),
            date=data.get('date'),
            subtotal=data.get('subtotal'),
            tax=data.get('tax'),
            total=data.get('total')
        )
        db.add(invoice)
        db.commit()
        invoice_id = invoice.id
        db.close()
        return invoice_id
    except Exception as e:
        print(f"Error al guardar en BD: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Intelli-Invoice Extractor CLI - Extrae datos de facturas"
    )
    parser.add_argument('file', help="Ruta al archivo PDF o imagen de la factura")
    parser.add_argument('--save-db', action='store_true', help="Guardar en base de datos")
    parser.add_argument('--output', '-o', help="Guardar resultado en archivo JSON")
    parser.add_argument('--verbose', '-v', action='store_true', help="Modo detallado")
    
    args = parser.parse_args()
    
    # Inicializar BD si se va a usar
    if args.save_db:
        init_db()
    
    # Paso 1: OCR
    if args.verbose:
        print(f"[1/3] Extrayendo texto de: {args.file}")
    
    try:
        text = ocr_file(args.file)
    except Exception as e:
        print(f"Error en OCR: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.verbose:
        print(f"✓ Texto extraído: {len(text)} caracteres")
    
    # Paso 2: Extraer campos
    if args.verbose:
        print("[2/3] Extrayendo campos estructurados...")
    
    data = extract_invoice_data(text)
    
    if args.verbose:
        print("✓ Campos extraídos")
    
    # Paso 3: Guardar/Mostrar
    if args.verbose:
        print("[3/3] Procesando salida...")
    
    # Guardar en BD si se solicitó
    if args.save_db:
        invoice_id = save_to_db(data)
        if invoice_id:
            data['saved_to_db'] = True
            data['db_id'] = invoice_id
            if args.verbose:
                print(f"✓ Guardado en BD con ID: {invoice_id}")
    
    # Guardar en archivo si se especificó
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if args.verbose:
            print(f"✓ Guardado en: {args.output}")
    
    # Mostrar resultado en consola
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()