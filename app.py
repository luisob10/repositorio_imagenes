import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
from PIL import Image
import re
import base64
import time

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
    return re.sub(r"[^A-Za-z0-9\-_]", "", str(c)).strip().upper()

def obtener_imagen_b64(file_id):
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

def obtener_extension(contenido):
    try:
        img = Image.open(BytesIO(contenido))
        formato = img.format.lower()
        return "jpg" if formato == "jpeg" else formato
    except Exception:
        return "jpg"

def generar_zip(encontrados, sufijos=None):
    if sufijos is None:
        sufijos = []
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipf:
        for codigo in encontrados:
            if sufijos and not any(codigo.endswith(s) for s in sufijos):
                continue
            file_id = drive_ids.get(codigo)
            if not file_id:
                continue
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    contenido = resp.content
                    ext = obtener_extension(contenido)
                    zipf.writestr(f"{codigo}.{ext}", contenido)
            except Exception:
                pass
    buffer.seek(0)
    return buffer

# ========================================
# 🧠 INTERFAZ PRINCIPAL
# ========================================
st.markdown("<div style='margin-top:-35px;'><h6>Ingresar códigos</h6></div>", unsafe_allow_html=True)
input_codigos = st.text_area("", height=160, label_visibility="collapsed", placeholder="Pega o escribe los códigos aquí...")

if st.button("🔍 Buscar"):
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
        st.stop()
    st.session_state["input_codigos"] = input_codigos.strip()
    st.session_state["buscando"] = True
    st.rerun()

# ========================================
# 🌀 PROGRESO MIENTRAS BUSCA
# ========================================
if st.session_state.get("buscando", False):
    codigos = [c.strip() for c in re.split(r"[,\n]+", st.session_state["input_codigos"]) if c.strip()]
    encontrados, no_encontrados = [], []

    total = len(codigos)
    progress_bar = st.progress(0)
    porcentaje_texto = st.empty()

    # Spinner visual personalizado (persona animada simulada)
    st.markdown("""
    <div style='text-align:center;'>
        <div class='loader'></div>
        <p style='color:white; font-size:18px;'>Buscando códigos...</p>
    </div>
    <style>
    .loader {
      border: 6px solid #f3f3f3;
      border-top: 6px solid #3498db;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: auto;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Actualización en tiempo real durante la búsqueda
    for i, codigo in enumerate(codigos):
        codigo_norm = normalizar_codigo(codigo)
        matches = [k for k in drive_ids.keys() if normalizar_codigo(k).startswith(codigo_norm)]
        if matches:
            encontrados.extend(matches)
        else:
            no_encontrados.append(codigo)

        porcentaje = int(((i + 1) / total) * 100)
        progress_bar.progress(porcentaje)
        porcentaje_texto.markdown(f"<h3 style='text-align:center; color:#00BFFF;'>⏳ {porcentaje}%</h3>", unsafe_allow_html=True)
        time.sleep(0.05)  # simula tiempo de procesamiento

    st.session_state["encontrados"] = sorted(set(encontrados))
    st.session_state["no_encontrados"] = no_encontrados
    st.session_state["buscando"] = False

    porcentaje_texto.markdown("<h3 style='text-align:center; color:lime;'>✅ 100%</h3>", unsafe_allow_html=True)
    time.sleep(0.5)
    st.rerun()

# ========================================
# 📋 RESULTADOS
# ========================================
if "encontrados" in st.session_state and not st.session_state.get("buscando", False):
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    col1, col2 = st.columns(2)

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

    with col2:
        st.markdown("<h5 style='font-size:15px;'>❌ Códigos no encontrados</h5>", unsafe_allow_html=True)
        for c in no_encontrados:
            st.markdown(f"<div class='codigo'>{c}</div>", unsafe_allow_html=True)
