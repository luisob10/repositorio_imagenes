import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
from PIL import Image
import base64
import re

# ========================================
# 🔐 LOGIN
# ========================================
PASSWORD = "123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    clave = st.text_input("🔑 Ingresa la clave de acceso", type="password", key="clave")
    if clave == PASSWORD:
        st.session_state["autenticado"] = True
        st.rerun()
    elif clave:
        st.error("❌ Clave incorrecta")
    st.stop()

# ========================================
# 📂 CARGAR CSV
# ========================================
try:
    df = pd.read_csv("imagenes.csv")
    drive_ids = dict(zip(df["codigo"], df["id"]))
except Exception as e:
    st.error(f"No se pudo cargar 'imagenes.csv': {e}")
    st.stop()

# ========================================
# 🔧 FUNCIONES
# ========================================
def normalizar_codigo(c):
    return re.sub(r"[^A-Za-z0-9\\-]", "", str(c)).strip().upper()

def obtener_imagen_b64(file_id):
    """Descarga imagen de Google Drive y la devuelve base64."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        pass
    return None

def generar_zip(encontrados, sufijo=None):
    """Genera ZIP con filtrado opcional por sufijo."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for key in encontrados:
            if sufijo and not key.endswith(f"_{sufijo}"):
                continue
            file_id = drive_ids.get(key)
            if not file_id:
                continue
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    zip_file.writestr(f"{key}.jpg", resp.content)
            except Exception:
                pass
    buffer.seek(0)
    return buffer

# ========================================
# 🧠 INTERFAZ PRINCIPAL
# ========================================
st.markdown("<h6 style='margin-top:-30px;'>Ingresar códigos</h6>", unsafe_allow_html=True)
input_codigos = st.text_area("", height=130, label_visibility="collapsed", placeholder="Pega o escribe los códigos...")

buscar = st.button("🔍 Buscar")

# ========================================
# 🔍 BÚSQUEDA
# ========================================
if buscar:
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
        st.stop()

    codigos = [normalizar_codigo(c) for c in re.split(r"[,\n]+", input_codigos) if c.strip()]
    encontrados, no_encontrados = [], []

    for codigo in codigos:
        coincidencias = [key for key in drive_ids.keys() if normalizar_codigo(key).startswith(codigo)]
        if coincidencias:
            encontrados.extend(coincidencias)
        else:
            no_encontrados.append(codigo)

    st.session_state["encontrados"] = sorted(list(set(encontrados)), key=lambda x: x.upper())
    st.session_state["no_encontrados"] = sorted(list(set(no_encontrados)), key=lambda x: x.upper())

# ========================================
# 🧾 RESULTADOS
# ========================================
if "encontrados" in st.session_state:
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    # ---- ESTILOS ----
    st.markdown("""
        <style>
        /* Ajuste general del espacio entre elementos */
        div[data-testid="stHorizontalBlock"] {
            gap: 0px !important;
        }
        div.block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
        }
        .element-container {
            margin-bottom: 0rem !important;
        }
        .stMarkdown {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Estilo de los códigos */
        .codigo-item {
            color: white !important;
            background-color: #222;
            padding: 4px 8px;
            margin: 1px 0;
            border-radius: 6px;
            font-size: 14px;
            display: inline-block;
            width: 100%;
            cursor: default;
        }

        h5 { 
            color: white; 
            margin-top: 2px !important; 
            margin-bottom: 4px !important; 
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="small")

    # ---- Códigos encontrados ----
    with col1:
        st.markdown("<h5 style='font-size:15px;'>✅ Códigos encontrados</h5>", unsafe_allow_html=True)
        if encontrados:
            html = ""
            for key in encontrados:
                file_id = drive_ids[key]
                img_b64 = obtener_imagen_b64(file_id)
                tooltip = f"<img src='data:image/jpeg;base64,{img_b64}' width='220'>" if img_b64 else "(Sin vista previa)"
                html += f"<div class='codigo-item' title='{tooltip}'>{key}</div>"
            st.components.v1.html(f"<div style='margin-bottom:0px'>{html}</div>", height=520, scrolling=True)
        else:
            st.markdown("<div style='color:white; font-size:15px;'>No se encontraron códigos</div>", unsafe_allow_html=True)

    # ---- Códigos no encontrados ----
    with col2:
        st.markdown("<h5 style='font-size:15px;'>❌ Códigos no encontrados</h5>", unsafe_allow_html=True)
        if no_encontrados:
            for codigo in no_encontrados:
                st.markdown(f"<div class='codigo-item'>{codigo}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:white; font-size:15px;'>No se encontraron códigos</div>", unsafe_allow_html=True)

    # ---- Botones de descarga (sin espacio adicional) ----
    if encontrados:
        st.markdown("<div style='margin-top:-10px;'></div>", unsafe_allow_html=True)

        colA, colB, colC = st.columns(3, gap="small")

        with colA:
            if any(k.endswith("_1") for k in encontrados):
                st.download_button(
                    "⬇️ Descargar IM1",
                    data=generar_zip(encontrados, "1"),
                    file_name="imagenes_IM1.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        with colB:
            if any(k.endswith("_2") for k in encontrados):
                st.download_button(
                    "⬇️ Descargar IM2",
                    data=generar_zip(encontrados, "2"),
                    file_name="imagenes_IM2.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        with colC:
            st.download_button(
                "⬇️ Descargar todo",
                data=generar_zip(encontrados),
                file_name="imagenes_todas.zip",
                mime="application/zip",
                use_container_width=True
            )
