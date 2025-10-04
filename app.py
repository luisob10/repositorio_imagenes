import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import base64
from zipfile import ZipFile

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "123"  # cámbiala a la tuya

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
# 📁 LECTURA DE ARCHIVO CSV DE IMÁGENES
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
# 🧠 FUNCIÓN PARA OBTENER IMÁGENES
# ========================================
def obtener_imagen(id_drive):
    url = f"https://drive.google.com/uc?export=download&id={id_drive}"
    resp = requests.get(url, stream=True)
    if resp.status_code == 200:
        return Image.open(BytesIO(resp.content))
    return None

# ========================================
# 🌐 INTERFAZ PRINCIPAL (estilo Photoshop)
# ========================================
st.markdown(
    """
    <style>
    .workspace {
        width: 50vw;
        height: 90vh;
        margin: auto;
        display: grid;
        grid-template-columns: 1fr 2fr 2fr;
        grid-gap: 10px;
        background: #2c2c2c;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.4);
    }
    .panel {
        background: #3a3a3a;
        color: white;
        border-radius: 8px;
        padding: 10px;
        overflow-y: auto;
        box-shadow: inset 0 0 5px rgba(0,0,0,0.6);
    }
    .panel h3 {
        margin-top: 0;
        font-size: 16px;
        border-bottom: 1px solid #555;
        padding-bottom: 4px;
    }
    .code-item {
        margin:5px; 
        padding:4px 6px; 
        border:1px solid #888; 
        border-radius:5px; 
        background:#2c2c2c;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='workspace'>", unsafe_allow_html=True)

# =====================
# 📥 Panel Ingreso
# =====================
with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### 📥 Ingresar códigos")
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
    st.markdown("</div>", unsafe_allow_html=True)

# =====================
# ✅ Panel Encontrados
# =====================
with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    if "encontrados" in st.session_state:
        encontrados = st.session_state["encontrados"]

        st.markdown(f"### ✅ Encontrados ({len(encontrados)})")

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

            for codigo, img in encontrados:
                st.markdown(f"<div class='code-item'>{codigo}</div>", unsafe_allow_html=True)
                st.image(img, width=180)
        else:
            st.info("No se encontró ningún código válido.")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================
# ❌ Panel No encontrados
# =====================
with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    if "no_encontrados" in st.session_state:
        no_encontrados = st.session_state["no_encontrados"]
        st.markdown(f"### ❌ No encontrados ({len(no_encontrados)})")
        for codigo in no_encontrados:
            st.markdown(f"<div class='code-item'>{codigo}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
