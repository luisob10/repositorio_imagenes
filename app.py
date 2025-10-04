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
# 🌐 INTERFAZ PRINCIPAL (estilo Photoshop reducido)
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
        border-radius: 6px;
        padding: 8px;
        overflow-y: auto;
        box-shadow: inset 0 0 4px rgba(0,0,0,0.5);
    }
    .panel h3 {
        font-size: 12px; /* 🔽 Mitad del tamaño */
        margin-top: 0;
        border-bottom: 1px solid #555;
        padding-bottom: 3px;
    }
    /* --- Hover preview --- */
    .code-hover {
        display:inline-block;
        margin:4px;
        padding:2px 5px;
        border:1px solid #4CAF50;
        border-radius:4px;
        cursor:pointer;
        background:#2c2c2c;
        position:relative;
    }
    .code-hover .preview {
        display:none;
        position:absolute;
        top:100%;
        left:0;
        z-index:100;
        background:white;
        border:1px solid #ccc;
        padding:2px;
    }
    .code-hover .preview img {
        width:120px;
        height:auto;
    }
    .code-hover:hover .preview {
        display:block;
    }
    /* --- No encontrados estilo simple --- */
    .code-miss {
        display:inline-block;
        margin:4px;
        padding:2px 5px;
        border:1px solid #aaa;
        border-radius:4px;
        background:#2c2c2c;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='workspace'>", unsafe_allow_html=True)

# =====================
# 📥 Panel Ingreso (más pequeño)
# =====================
with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### 📥 Ingresar códigos")
    input_codigos = st.text_area(
        "Códigos desde Excel",
        height=200,  # 🔽 más bajo
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
# ✅ Panel Encontrados (hover con preview)
# =====================
with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    if "encontrados" in st.session_state:
        encontrados = st.session_state["encontrados"]

        st.markdown(f"### ✅ Encontrados ({len(encontrados)})")

        if encontrados:
            # Botón ZIP
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

            # Códigos con hover preview
            html_codes = ""
            for codigo, img in encontrados:
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                html_codes += f"""
                <div class="code-hover">
                    {codigo}
                    <div class="preview">
                        <img src="data:image/jpeg;base64,{img_base64}"/>
                    </div>
                </div>
                """
            st.markdown(html_codes, unsafe_allow_html=True)
        else:
            st.info("No se encontró ningún código válido.")
    st.markdown("</div>", unsafe_allow_html=True)

# =====================
# ❌ Panel No encontrados (sin rectángulo grande)
# =====================
with st.container():
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    if "no_encontrados" in st.session_state:
        no_encontrados = st.session_state["no_encontrados"]
        st.markdown(f"### ❌ No encontrados ({len(no_encontrados)})")
        html_codes = "".join([f"<span class='code-miss'>{c}</span>" for c in no_encontrados])
        st.markdown(html_codes, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
