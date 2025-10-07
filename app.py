import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
from PIL import Image
import re
import base64

# ========================================
# 🔐 LOGIN
# ========================================
PASSWORD = "123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    clave = st.text_input("🔑 Ingresa la clave de acceso", type="password", key="clave_input")
    if clave == PASSWORD:
        st.session_state["autenticado"] = True
        st.rerun()
    elif clave and clave != PASSWORD:
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
# ⚙️ FUNCIONES
# ========================================
def normalizar_codigo(c):
    """Limpia el código y lo convierte a mayúsculas para comparar sin importar el caso."""
    return re.sub(r"[^A-Za-z0-9\-]", "", str(c)).strip().upper()

def obtener_imagen_b64(file_id):
    """Descarga una imagen desde Google Drive y la convierte a base64."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content)).convert("RGB")
            img.thumbnail((250, 250))
            buf = BytesIO()
            img.save(buf, format="JPEG")
            return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

def generar_zip(encontrados, sufijo=None):
    """Genera un archivo ZIP con las imágenes encontradas (IM1, IM2 o todas)."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipf:
        for codigo in encontrados:
            if sufijo and not codigo.endswith(f"_{sufijo}"):
                continue
            file_id = drive_ids.get(codigo)
            if not file_id:
                continue
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    zipf.writestr(f"{codigo}.jpg", resp.content)
            except Exception:
                pass
    buffer.seek(0)
    return buffer

# ========================================
# 🧠 INTERFAZ PRINCIPAL
# ========================================
st.markdown("<div style='margin-top:-35px;'><h6>Ingresar códigos</h6></div>", unsafe_allow_html=True)
input_codigos = st.text_area("", height=160, label_visibility="collapsed", placeholder="Pega o escribe los códigos aquí...")

# --- Botón buscar ---
if st.button("🔍 Buscar"):
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
        st.stop()

    codigos = [c.strip() for c in re.split(r"[,\n]+", input_codigos) if c.strip()]
    encontrados, no_encontrados = [], []

    # 🔎 Comparación sin importar mayúsculas/minúsculas
    for codigo in codigos:
        codigo_norm = normalizar_codigo(codigo)
        matches = [k for k in drive_ids.keys() if normalizar_codigo(k).startswith(codigo_norm)]
        if matches:
            encontrados.extend(matches)
        else:
            no_encontrados.append(codigo)

    st.session_state["encontrados"] = sorted(set(encontrados))
    st.session_state["no_encontrados"] = no_encontrados
    st.session_state["ultima_busqueda"] = input_codigos.strip()

# ========================================
# 📋 MOSTRAR RESULTADOS
# ========================================
if "encontrados" in st.session_state:
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    col1, col2 = st.columns(2)

    # --- Estilos CSS para los códigos ---
    st.markdown("""
        <style>
        .codigo {
            color: white;
            font-size: 13px;
            display: block;
            margin: 2px 0;
            position: relative;
            cursor: pointer;
        }
        .tooltip-img {
            visibility: hidden;
            width: 250px;
            height: 250px;
            background-color: #000;
            border: 2px solid #555;
            border-radius: 8px;
            position: absolute;
            z-index: 999;
            top: -10px;
            left: 105%;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .codigo:hover .tooltip-img {
            visibility: visible;
            opacity: 1;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Columna izquierda: encontrados ---
    with col1:
        st.markdown("<h5 style='font-size:15px;'>✅ Códigos encontrados</h5>", unsafe_allow_html=True)
        html = ""
        for codigo in encontrados:
            file_id = drive_ids.get(codigo)
            img_b64 = obtener_imagen_b64(file_id)
            if img_b64:
                html += f"""
                <div class="codigo">{codigo}
                    <div class="tooltip-img">
                        <img src="data:image/jpeg;base64,{img_b64}" width="250" height="250" style="object-fit:contain;"/>
                    </div>
                </div>
                """
            else:
                html += f"<div class='codigo'>{codigo}</div>"
        st.markdown(html, unsafe_allow_html=True)

    # --- Columna derecha: no encontrados ---
    with col2:
        st.markdown("<h5 style='font-size:15px;'>❌ Códigos no encontrados</h5>", unsafe_allow_html=True)
        for c in no_encontrados:
            st.markdown(f"<div class='codigo'>{c}</div>", unsafe_allow_html=True)

    # ========================================
    # 📦 DESCARGAS (sin disparar nueva búsqueda)
    # ========================================
    colA, colB, colC = st.columns(3)

    with colA:
        if any(k.endswith("_1") for k in encontrados):
            buffer1 = generar_zip(encontrados, "1")
            st.download_button(
                "⬇️ Descargar IM1",
                buffer1,
                "imagenes_IM1.zip",
                mime="application/zip",
                use_container_width=True,
                key="desc1"
            )

    with colB:
        if any(k.endswith("_2") for k in encontrados):
            buffer2 = generar_zip(encontrados, "2")
            st.download_button(
                "⬇️ Descargar IM2",
                buffer2,
                "imagenes_IM2.zip",
                mime="application/zip",
                use_container_width=True,
                key="desc2"
            )

    with colC:
        buffer_all = generar_zip(encontrados)
        st.download_button(
            "⬇️ Descargar todo",
            buffer_all,
            "imagenes_todas.zip",
            mime="application/zip",
            use_container_width=True,
            key="desc_all"
        )
