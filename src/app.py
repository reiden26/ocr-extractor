import streamlit as st
from ocr_utils import ocr_file
import json

st.title("Intelli-Invoice Extractor (demo)")

uploaded = st.file_uploader("Sube una factura (PDF/JPG/PNG)", type=['pdf','png','jpg','jpeg'])
if uploaded is not None:
    with open("temp_upload", "wb") as f:
        f.write(uploaded.getbuffer())
    text = ocr_file("temp_upload")
    st.subheader("Texto extraído")
    st.text_area("ocr", text, height=300)
    # aquí llamarías a tu parser/extractor
    st.download_button("Descargar JSON", data=json.dumps({"raw_text": text}, ensure_ascii=False, indent=2), file_name="invoice.json")
