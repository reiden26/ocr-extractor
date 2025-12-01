import streamlit as st
import sys
import os
import json

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr_utils import ocr_file
from extractor import extract_invoice_data
from db import SessionLocal, Invoice, init_db
from local_ai_agent import refinar_datos_factura
import streamlit.components.v1 as components

# Inicializar BD
init_db()

# Estado de sesión para IA local
if "raw_text" not in st.session_state:
    st.session_state.raw_text = None
if "data_inicial" not in st.session_state:
    st.session_state.data_inicial = None
if "data_refinada" not in st.session_state:
    st.session_state.data_refinada = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🧾 Intelli-Invoice Extractor")
st.markdown("Extrae datos estructurados de facturas PDF o imágenes")

uploaded = st.file_uploader("📁 Sube una factura (PDF/JPG/PNG)", type=['pdf','png','jpg','jpeg'])

if uploaded is not None:
    # Guardar archivo temporal con extensión correcta
    file_extension = os.path.splitext(uploaded.name)[1]
    temp_path = f"temp_upload{file_extension}"
    with open(temp_path, "wb") as f:
        f.write(uploaded.getbuffer())
    
    with st.spinner("⚙️ Procesando con OCR..."):
        # Extraer texto con OCR
        text = ocr_file(temp_path)

    # Guardar en estado para IA y chat
    st.session_state.raw_text = text

    with st.spinner("🤖 Extrayendo campos inteligentemente..."):
        # Extraer datos estructurados (método clásico)
        data = extract_invoice_data(text)

    st.session_state.data_inicial = data
    # Si se sube una nueva factura, limpiar refinamiento y chat previos
    st.session_state.data_refinada = None
    st.session_state.chat_history = []

    # Mostrar texto extraído en expander
    with st.expander("📄 Ver texto OCR completo"):
        st.text_area("Texto extraído", text, height=200)

    st.success("✅ Extracción completada")

    # Elegir qué datos mostrar (refinados por IA si existen)
    data_to_show = st.session_state.data_refinada or data

    # Datos estructurados como JSON
    with st.expander("📊 Ver datos estructurados (JSON)"):
        st.json(data_to_show)

    # Sección de IA local (LM Studio)
    st.subheader("🤖 IA local (LM Studio)")

    if st.session_state.data_refinada:
        with st.expander("📦 Ver JSON refinado por IA"):
            st.json(st.session_state.data_refinada)

    # Panel de opciones al final
    with st.expander("⚙️ Opciones"):
        # 1) Refinar datos con IA local
        if st.button("✨ Refinar datos con IA local"):
            try:
                with st.spinner("Llamando a LM Studio para refinar la factura..."):
                    refined = refinar_datos_factura(
                        st.session_state.raw_text,
                        st.session_state.data_inicial,
                    )
                st.session_state.data_refinada = refined
                st.success("✅ Datos refinados con IA local")
            except Exception as e:
                st.error(f"❌ No se pudo refinar con IA local: {e}")

        # 2) Descargar JSON (usa datos refinados si existen)
        datos_descarga = st.session_state.data_refinada or st.session_state.data_inicial
        json_data = json.dumps(datos_descarga, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 Descargar JSON",
            data=json_data,
            file_name=f"invoice_{datos_descarga.get('invoice_number', 'unknown')}.json",
            mime="application/json"
        )

        # 3) Guardar en BD (usa datos refinados si existen)
        if st.button("💾 Guardar en Base de Datos"):
            try:
                db = SessionLocal()
                invoice = Invoice(
                    invoice_number=datos_descarga.get('invoice_number'),
                    supplier=datos_descarga.get('supplier'),
                    nit=datos_descarga.get('nit'),
                    date=datos_descarga.get('date'),
                    subtotal=datos_descarga.get('subtotal'),
                    tax=datos_descarga.get('tax'),
                    total=datos_descarga.get('total')
                )
                db.add(invoice)
                db.commit()
                db.close()
                st.success("✅ Guardado en base de datos")
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

    # Limpiar archivo temporal
    if os.path.exists(temp_path):
        os.remove(temp_path)

# Sidebar con información
st.sidebar.header("ℹ️ Información")
st.sidebar.markdown("""
**Formatos soportados:**
- PDF
- JPG/JPEG
- PNG

**Campos extraídos:**
- Número de Factura
- Fecha de Emisión
- Proveedor
- NIT
- Subtotal
- IVA
- Total

**Tecnologías:**
- Tesseract OCR
- spaCy NLP
- SQLite
""")

# Mostrar facturas guardadas
st.sidebar.header("📚 Facturas en BD")
try:
    db = SessionLocal()
    invoices = db.query(Invoice).all()
    db.close()
    st.sidebar.write(f"Total: {len(invoices)} facturas")
    if invoices:
        for inv in invoices[-5:]:  # Últimas 5
            st.sidebar.text(f"• {inv.invoice_number or 'N/A'}")
except:
    st.sidebar.write("BD no inicializada")

# Widget de chat flotante (HTML/JS) usando el servidor FastAPI en /chat
if st.session_state.raw_text and st.session_state.data_inicial:
    datos_chat = st.session_state.data_refinada or st.session_state.data_inicial
    raw_text_js = json.dumps(st.session_state.raw_text)
    datos_chat_js = json.dumps(datos_chat, ensure_ascii=False)

    html_chat = f"""
    <style>
    .invoice-chat-fab {{
        position: fixed;
        right: 20px;
        bottom: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #4b8bf4;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        font-size: 24px;
    }}
    .invoice-chat-window {{
        position: fixed;
        right: 20px;
        bottom: 90px;
        width: 320px;
        max-height: 420px;
        background: #111827;
        color: #f9fafb;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        display: none;
        flex-direction: column;
        overflow: hidden;
        z-index: 9999;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .invoice-chat-header {{
        padding: 10px 14px;
        background: #1f2937;
        border-bottom: 1px solid #374151;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 14px;
        font-weight: 600;
    }}
    .invoice-chat-header span {{
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .invoice-chat-header button {{
        background: transparent;
        border: none;
        color: #9ca3af;
        cursor: pointer;
        font-size: 16px;
    }}
    .invoice-chat-messages {{
        padding: 10px;
        overflow-y: auto;
        flex: 1;
        font-size: 13px;
    }}
    .invoice-chat-input {{
        padding: 8px;
        border-top: 1px solid #374151;
        display: flex;
        gap: 6px;
        background: #111827;
    }}
    .invoice-chat-input input {{
        flex: 1;
        padding: 6px 8px;
        border-radius: 6px;
        border: 1px solid #4b5563;
        background: #020617;
        color: #f9fafb;
        font-size: 13px;
    }}
    .invoice-chat-input button {{
        padding: 6px 10px;
        border-radius: 6px;
        border: none;
        background: #4b8bf4;
        color: white;
        cursor: pointer;
        font-size: 13px;
    }}
    .invoice-msg-user {{
        background: #2563eb;
        color: white;
        padding: 6px 8px;
        border-radius: 10px;
        margin-bottom: 6px;
        margin-left: 40px;
    }}
    .invoice-msg-bot {{
        background: #111827;
        border: 1px solid #374151;
        padding: 6px 8px;
        border-radius: 10px;
        margin-bottom: 6px;
        margin-right: 40px;
    }}
    </style>
    <div class="invoice-chat-window" id="invoice-chat-window">
      <div class="invoice-chat-header">
        <span>💬 Intelli-Invoice</span>
        <button onclick="document.getElementById('invoice-chat-window').style.display='none'">✕</button>
      </div>
      <div class="invoice-chat-messages" id="invoice-chat-messages">
        <div class="invoice-msg-bot">Estoy listo para responder preguntas sobre esta factura.</div>
      </div>
      <div class="invoice-chat-input">
        <input id="invoice-chat-input" type="text" placeholder="Escribe tu pregunta..." />
        <button onclick="window.invoiceSend()">Enviar</button>
      </div>
    </div>
    <div class="invoice-chat-fab" onclick="document.getElementById('invoice-chat-window').style.display='flex'">
      💬
    </div>
    <script>
    const RAW_TEXT = {raw_text_js};
    const DATA_STRUCTURED = {datos_chat_js};

    async function callInvoiceChat(question) {{
      const resp = await fetch("http://127.0.0.1:8000/chat", {{
        method: "POST",
        headers: {{
          "Content-Type": "application/json"
        }},
        body: JSON.stringify({{
          question,
          raw_text: RAW_TEXT,
          data_structured: DATA_STRUCTURED
        }})
      }});
      if (!resp.ok) {{
        throw new Error("Error HTTP " + resp.status);
      }}
      const data = await resp.json();
      return data.answer || "";
    }}

    function appendMsg(text, cls) {{
      const box = document.getElementById("invoice-chat-messages");
      const div = document.createElement("div");
      div.className = cls;
      div.textContent = text;
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
    }}

    window.invoiceSend = async function() {{
      const input = document.getElementById("invoice-chat-input");
      const q = input.value.trim();
      if (!q) return;
      appendMsg(q, "invoice-msg-user");
      input.value = "";
      try {{
        appendMsg("Pensando...", "invoice-msg-bot");
        const answer = await callInvoiceChat(q);
        const box = document.getElementById("invoice-chat-messages");
        box.removeChild(box.lastChild); // quitar "Pensando..."
        appendMsg(answer || "No se pudo obtener respuesta.", "invoice-msg-bot");
      }} catch (e) {{
        appendMsg("Error al llamar al servidor de chat: " + e.message, "invoice-msg-bot");
      }}
    }}
    </script>
    """

    # Renderizar el widget. Usamos una altura pequeña del iframe pero
    # suficiente para que el chat flotante sea visible dentro de la página.
    components.html(html_chat, height=500, width=0)