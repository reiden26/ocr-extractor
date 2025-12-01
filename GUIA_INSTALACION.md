# 🚀 Guía de Instalación y Ejecución - Intelli-Invoice Extractor

## 📋 Requisitos Previos

### 1. Python 3.8+
Verifica tu versión:
```bash
python --version
# o
python3 --version
```

### 2. Tesseract OCR
Tesseract es el motor OCR que necesitamos instalar en el sistema.

#### En Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-spa  # Idioma español
sudo apt install libtesseract-dev
```

#### En macOS:
```bash
brew install tesseract
brew install tesseract-lang  # Idiomas adicionales
```

#### En Windows:
1. Descargar instalador desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Ejecutar el instalador
3. Agregar Tesseract al PATH del sistema

Verificar instalación:
```bash
tesseract --version
```

### 3. Poppler (para convertir PDF a imágenes)

#### En Ubuntu/Debian:
```bash
sudo apt install poppler-utils
```

#### En macOS:
```bash
brew install poppler
```

#### En Windows:
1. Descargar desde: http://blog.alivate.com.au/poppler-windows/
2. Extraer y agregar `bin/` al PATH

---

## 🔧 Instalación del Proyecto

### Paso 1: Clonar o navegar al proyecto
```bash
cd /ruta/a/Intelli-Invoice-Extractor
```

### Paso 2: Crear entorno virtual
```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# En Linux/macOS:
source .venv/bin/activate

# En Windows:
.venv\Scripts\activate
```

### Paso 3: Instalar dependencias Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Descargar modelo de spaCy
```bash
python -m spacy download es_core_news_sm
```

### Paso 5: Crear estructura de directorios
```bash
mkdir -p data
mkdir -p scripts
```

### Paso 6: Inicializar la base de datos
```bash
# Asegúrate de estar en el directorio raíz del proyecto
python scripts/init_db.py
```

Deberías ver:
```
🔧 Inicializando base de datos SQLite...
✓ Directorio data: /ruta/data
✓ Tablas creadas
✓ Tablas en BD: invoices

📋 Esquema de tabla 'invoices':
  - id: INTEGER
  - invoice_number: VARCHAR
  - supplier: VARCHAR
  - nit: VARCHAR
  - date: VARCHAR
  - subtotal: VARCHAR
  - tax: VARCHAR
  - total: VARCHAR

✅ Base de datos lista para usar
📍 Ubicación: data/invoices.db
```

---

## 🏃 Ejecutar el Proyecto

### Opción 1: Interfaz Web (Streamlit) - Recomendado

```bash
streamlit run src/app.py
```

Se abrirá automáticamente en tu navegador en `http://localhost:8501`

**Uso:**
1. Sube una factura (PDF, JPG, PNG)
2. Espera el procesamiento
3. Revisa los campos extraídos
4. Descarga JSON o guarda en BD

---

### Opción 2: Línea de Comandos (CLI)

#### Uso básico (solo mostrar datos):
```bash
python src/cli_app.py facturas/ejemplo.pdf
```

#### Con modo verbose:
```bash
python src/cli_app.py facturas/ejemplo.pdf --verbose
```

#### Guardar en base de datos:
```bash
python src/cli_app.py facturas/ejemplo.pdf --save-db --verbose
```

#### Guardar resultado en JSON:
```bash
python src/cli_app.py facturas/ejemplo.pdf --output resultado.json
```

#### Todo combinado:
```bash
python src/cli_app.py facturas/ejemplo.pdf --save-db --output resultado.json --verbose
```

---

## 📁 Estructura del Proyecto

```
Intelli-Invoice-Extractor/
├── .gitignore
├── README.md
├── requirements.txt
├── GUIA_INSTALACION.md         # Este archivo
│
├── data/                        # Base de datos SQLite
│   └── invoices.db             # Creado automáticamente
│
├── scripts/
│   └── init_db.py              # Script de inicialización de BD
│
└── src/
    ├── app.py                  # Interfaz web Streamlit
    ├── cli_app.py              # Interfaz CLI
    ├── ocr_utils.py            # Funciones OCR
    ├── extractor.py            # Extracción inteligente
    └── db.py                   # Modelos de base de datos
```

---

## 🧪 Probar el Sistema

### 1. Crear factura de prueba

Puedes crear una factura de prueba simple en un documento de texto y convertirlo a imagen:

**ejemplo_factura.txt:**
```
EMPRESA XYZ S.A.S
NIT: 900.123.456-7

FACTURA No: FAC-2024-001
Fecha: 15/11/2024

Cliente: Juan Pérez
NIT/CC: 123456789

DESCRIPCIÓN
----------------------------------------
Producto A      $100,000
Producto B      $50,000

Subtotal:       $150,000
IVA (19%):      $28,500
Total:          $178,500
```

Convierte este texto a imagen o PDF y pruébalo.

### 2. Ejecutar prueba rápida

```bash
# Con Streamlit
streamlit run src/app.py
# Luego sube tu factura de prueba

# O con CLI
python src/cli_app.py tu_factura.pdf --verbose
```

---

## ❓ Solución de Problemas Comunes

### Error: "TesseractNotFoundError"
- **Causa:** Tesseract no está instalado o no está en el PATH
- **Solución:** Instala Tesseract y verifica con `tesseract --version`

### Error: "Unable to get page count. Is poppler installed?"
- **Causa:** Poppler no está instalado
- **Solución:** Instala poppler-utils según tu sistema operativo

### Error: "Can't find model 'es_core_news_sm'"
- **Causa:** Modelo de spaCy no descargado
- **Solución:** `python -m spacy download es_core_news_sm`

### La BD no se crea
- **Solución:** Verifica que el directorio `data/` existe o ejecuta:
```bash
mkdir -p data
python scripts/init_db.py
```

### Error de permisos en Linux
```bash
chmod +x scripts/init_db.py
```

---

## 🎯 Próximos Pasos

1. **Mejorar la extracción**: Entrena modelos personalizados con tus facturas
2. **Agregar más campos**: Productos, cantidades, direcciones, etc.
3. **API REST**: Crea una API con FastAPI para integrar con otros sistemas
4. **Dashboard**: Visualiza estadísticas de facturas procesadas
5. **Exportar a Excel**: Genera reportes automáticos

---

## 📚 Recursos Adicionales

- **Tesseract OCR:** https://github.com/tesseract-ocr/tesseract
- **spaCy:** https://spacy.io/
- **Streamlit:** https://streamlit.io/
- **SQLAlchemy:** https://www.sqlalchemy.org/

---

## 🆘 Soporte

Si encuentras problemas:
1. Verifica que todos los requisitos estén instalados
2. Revisa los logs en modo `--verbose`
3. Consulta la documentación de cada herramienta
4. Abre un issue en el repositorio

---

✅ **¡Listo! Tu sistema Intelli-Invoice Extractor está funcionando.**