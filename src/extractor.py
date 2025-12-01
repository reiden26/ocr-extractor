import re
from datetime import datetime
import spacy

# Cargar modelo de spaCy (si está disponible)
try:
    nlp = spacy.load("es_core_news_sm")
except:
    nlp = None
    print("Advertencia: Modelo spaCy no encontrado. Usa: python -m spacy download es_core_news_sm")

class InvoiceExtractor:
    """Extrae campos estructurados de texto OCR de facturas"""
    
    def __init__(self, text):
        self.text = text
        self.lines = text.splitlines()
        
    def extract_all(self):
        """Extrae todos los campos de la factura"""
        return {
            "invoice_number": self.extract_invoice_number(),
            "date": self.extract_date(),
            "supplier": self.extract_supplier(),
            "nit": self.extract_nit(),
            "subtotal": self.extract_subtotal(),
            "tax": self.extract_tax(),
            "total": self.extract_total(),
            "raw_text": self.text
        }
    
    def extract_invoice_number(self):
        """Extrae el número de factura"""
        patterns = [
            r'(?:factura|invoice|fact\.?)\s*(?:n[oº°]?\.?|#|num\.?)?[\s:]*([A-Z0-9\-]+)',
            r'(?:n[oº°]\.?\s*factura|fact\.?\s*n[oº°]\.?)[\s:]*([A-Z0-9\-]+)',
            r'(?:^|\s)([A-Z]{2,4}\-?\d{6,})',  # Formato común: ABC-123456
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def extract_date(self):
        """Extrae la fecha de emisión"""
        patterns = [
            r'(?:fecha|date|f\.|emisión)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                return self._normalize_date(date_str)
        return None
    
    def _normalize_date(self, date_str):
        """Normaliza diferentes formatos de fecha"""
        # Intentar parsear diferentes formatos
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except:
                continue
        return date_str
    
    def extract_supplier(self):
        """Extrae el nombre del proveedor"""
        # Buscar usando spaCy si está disponible
        if nlp:
            doc = nlp(self.text[:500])  # Primeros 500 caracteres
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                return orgs[0]
        
        # Fallback: buscar líneas superiores con palabras clave
        for i, line in enumerate(self.lines[:15]):  # Primeras 15 líneas
            if any(keyword in line.upper() for keyword in ['S.A.', 'LTDA', 'S.A.S', 'S.R.L', 'CIA', 'COMPANY']):
                return line.strip()
        
        # Último recurso: primera línea no vacía
        for line in self.lines[:10]:
            if line.strip() and len(line.strip()) > 3:
                return line.strip()
        return None
    
    def extract_nit(self):
        """Extrae el NIT o identificación fiscal"""
        patterns = [
            r'(?:nit|ruc|rfc|cuit|tax\s*id)[\s:]*([0-9\.\-]{7,15})',
            r'(?:identificación|id\.?)[\s:]*([0-9\.\-]{7,15})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def extract_subtotal(self):
        """Extrae el subtotal"""
        return self._extract_amount(['subtotal', 'sub-total', 'base\s+imponible'])
    
    def extract_tax(self):
        """Extrae el impuesto (IVA, TAX, etc.)"""
        return self._extract_amount(['iva', 'tax', 'impuesto', 'vat'])
    
    def extract_total(self):
        """Extrae el total"""
        return self._extract_amount(['total', 'total\s+a\s+pagar', 'importe\s+total', 'monto\s+total'])
    
    def _extract_amount(self, keywords):
        """Extrae un monto monetario dado una lista de palabras clave"""
        for keyword in keywords:
            # Patrón mejorado para capturar montos
            pattern = rf'(?:{keyword})[\s:$]*([0-9]+[,.]?[0-9]*\.?[0-9]{{2}})'
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                amount = match.group(1).strip()
                # Normalizar formato (reemplazar comas por puntos)
                amount = amount.replace(',', '')
                return amount
        return None


def extract_invoice_data(text):
    """Función helper para extraer datos de una factura"""
    extractor = InvoiceExtractor(text)
    return extractor.extract_all()