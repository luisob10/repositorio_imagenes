import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import base64
from zipfile import ZipFile

# ========================================
# 🔐 LOGIN
# ========================================
PASSWORD = "123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    with st.form("login_form"):
        clave = st.text_input("🔐 Ingresa la clave de acceso", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    st.stop()

# ========================================
# 📁 LECTURA CSV
# ========================================
@st.cache_data
def cargar_csv():
    try:
        df = pd.read_csv("imagenes.csv")
        return dict(zip(df["codigo"], df["id"]))
    except Exception as e:
        st.error(f"No se pudo cargar 'imagenes.csv': {e}")
        return {}

drive_ids = cargar_csv()

# ========================================
# 🧠 OBTENER IMAGEN
# ========================================
def obtener_imagen(id_drive):
    url = f"https://drive.google.com/uc?export=download&id={id_drive}"
    resp = requests.get(url, stream=True)
    if resp.status_code == 200:
        return Image.open(BytesIO(resp.content))
    return None

# ========================================
# 🌐 AJUSTES VISUALES
# ========================================
st.markdown(
    """
    <style>
    /* Layout ancho completo */
    .block-container {
        max-width: 100% !important;
        padding: 1rem 2rem;
    }
    /* Estilo tipo Photoshop */
    body {
        background-color: #1e1e1e;
        color: #f0f0f0;
        font-family: "Segoe UI", sans-serif;
    }
    .stTextArea textarea {
        background-color: #2d2d2d;
        color: #f0f0f0;
        border-radius: 8px;
        font-size: 14px;
    }
    .code-box {
        display:inline-block;
        position:relative;
        margin:8px;
        padding:6px 10px;
        border:1px solid #4CAF50;
        border-radius:6px;
        background-color:#2b2b2b;
        box-shadow:0 2px 5px rgba(0,0,0,0.3);
        cursor:pointer;
        transition:all 0.2s ease-in-out;
    }
    .code-box:hover {
        background-color:#3a3a3a;
        transform:scale(1.05);
    }
    .code-box .preview {
        display:none;
        position:absolute;
        top:0;
        left:110%;
        z-index:100;
        border:1px solid #ccc;
        background:white;
        padding:4px;
        border-radius:6px;
        box-shadow:0 4px 12px rgba(0,0,0,0.5);
    }
    .code-box .preview img {
        width:350px !important;
        max-width:350px !important;
        height:auto !important;
        border-radius:4px;
    }
    .code-box:hover .preview {
        display:block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ========================================
# 🖼️ INTERFAZ PRINCIPAL
# ========================================
col_input, col_result = st.columns([1, 2])

with col_input:
    st.markdown("## 📥 Ingresar códigos")
    input_codigos = st.text_area(
        "Códigos desde Excel", 
        height=600,  
        label_visibility="collapsed"
    )

    if st.button("Buscar"):
        if not input_codigos.strip():
            st.warning("Por favor ingresa al menos un código.")
        else:
            codigos = [c.strip() for c in input_codigos.replace("\n", ",").split(",") if c.strip()]
            encontrados = []
            no_encontrados = []

            for codigo in codigos:
                if codigo in drive_ids:
                    img = obtener_imagen(drive_ids[codigo])
                    if img:
                        encontrados.append((codigo, img))
                    else:
                        no_encontrados.append(codigo)
                else:
                    no_encontrados.append(codigo)

            st.session_state["encontrados"] = encontrados
            st.session_state["no_encontrados"] = no_encontrados

with col_result:
    if "encontrados" in st.session_state:
        encontrados = st.session_state["encontrados"]
        no_encontrados = st.session_state["no_encontrados"]

        # --- Header + botón descargar ---
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### ✅ Códigos encontrados ({len(encontrados)})")
        with col2:
            if encontrados:
                zip_buffer = BytesIO()
                with ZipFile(zip_buffer, "w") as zip_file:
                    for codigo, img in encontrados:
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="JPEG")
                        zip_file.writestr(f"{codigo}.jpg", img_bytes.getvalue())
                zip_buffer.seek(0)
                st.download_button(
                    label="📦 Descargar todo",
                    data=zip_buffer,
                    file_name="imagenes_encontradas.zip",
                    mime="application/zip",
                    key="descargar_zip"
                )

        # --- Grid de encontrados ---
        if encontrados:
            html_codes = "<div style='display:flex; flex-wrap:wrap;'>"
            for codigo, img in encontrados:
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                html_codes += f"""
                <div class="code-box">
                    {codigo}
                    <div class="preview">
                        <img src="data:image/jpeg;base64,{img_base64}"/>
                    </div>
                </div>
                """
            html_codes += "</div>"
            st.markdown(html_codes, unsafe_allow_html=True)
        else:
            st.info("No se encontró ningún código válido.")

        # --- Mostrar no encontrados ---
        if no_encontrados:
            st.markdown(f"### ❌ Códigos no encontrados ({len(no_encontrados)})")
            html_no = "<div style='display:flex; flex-wrap:wrap;'>"
            for codigo in no_encontrados:
                html_no += f"<div style='margin:6px; padding:6px 10px; border:1px solid #aaa; border-radius:6px; background:#3a3a3a;'>{codigo}</div>"
            html_no += "</div>"
            st.markdown(html_no, unsafe_allow_html=True)
