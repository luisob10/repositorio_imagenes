import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
from PIL import Image
import re
import base64
import time

# ===============================
# 🔐 LOGIN
# ===============================
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

# ===============================
# 📂 CARGAR CSV
# ===============================
try:
    df = pd.read_csv("imagenes.csv")
    drive_ids = dict(zip(df["codigo"], df["id"]))
except Exception as e:
    st.error(f"No se pudo cargar 'imagenes.csv': {e}")
    st.stop()

# ===============================
# ⚙️ FUNCIONES
# ===============================
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

# ===============================
# 🧠 INTERFAZ
# ===============================
st.markdown("<h6>Ingresar códigos</h6>", unsafe_allow_html=True)
input_codigos = st.text_area("", height=160, label_visibility="collapsed", placeholder="Pega o escribe los códigos aquí...")

# Creamos un contenedor para la barra (visible de inmediato)
progress_placeholder = st.empty()
text_placeholder = st.empty()

if st.button("🔍 Buscar"):
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
        st.stop()

    codigos = [c.strip() for c in re.split(r"[,\n]+", input_codigos) if c.strip()]
    encontrados, no_encontrados = [], []

    progress_bar = progress_placeholder.progress(0)
    total = len(codigos)

    # 🔁 Bucle con actualización visual garantizada
    for i, codigo in enumerate(codigos, start=1):
        codigo_norm = normalizar_codigo(codigo)
        matches = [k for k in drive_ids.keys() if normalizar_codigo(k).startswith(codigo_norm)]
        if matches:
            encontrados.extend(matches)
        else:
            no_encontrados.append(codigo)

        percent = int(i / total * 100)
        progress_bar.progress(percent)
        text_placeholder.text(f"🔎 Buscando códigos... {percent}%")
        time.sleep(0.02)  # 👈 este pequeño delay permite que Streamlit ACTUALICE

    # Limpiamos la barra
    progress_placeholder.empty()
    text_placeholder.empty()
    st.success("✅ Búsqueda completada.")

    st.session_state["encontrados"] = encontrados
    st.session_state["no_encontrados"] = no_encontrados

# ===============================
# 📋 MOSTRAR RESULTADOS
# ===============================
if "encontrados" in st.session_state:
    st.subheader("Resultados de la búsqueda")
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    st.write("✅ Encontrados:", len(encontrados))
    st.write("❌ No encontrados:", len(no_encontrados))

    st.dataframe(pd.DataFrame({"Encontrados": encontrados}))
    st.dataframe(pd.DataFrame({"No encontrados": no_encontrados}))
