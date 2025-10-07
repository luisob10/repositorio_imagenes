import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
import re
from PIL import Image

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    clave = st.text_input("🔑 Ingresa la clave de acceso", type="password", key="clave_input")

    if st.session_state.get("last_clave") != clave and clave:
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.session_state["last_clave"] = clave
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    elif st.button("Entrar"):
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
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
# 🔧 FUNCIONES AUXILIARES
# ========================================
def normalizar_codigo(c):
    return re.sub(r"[^A-Za-z0-9\-]", "", str(c)).strip().upper()

def generar_zip(encontrados, sufijo=None):
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
st.markdown("<div style='margin-top:-35px;'><h6>Ingresar códigos</h6></div>", unsafe_allow_html=True)
input_codigos = st.text_area("", height=160, label_visibility="collapsed", placeholder="Pega o escribe los códigos aquí...")

buscar = st.button("🔍 Buscar")

# ========================================
# 🔍 BÚSQUEDA
# ========================================
if buscar:
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
        st.stop()

    codigos = [normalizar_codigo(c) for c in re.split(r"[,\n]+", input_codigos) if c.strip()]
    encontrados = []
    no_encontrados = []

    for codigo in codigos:
        coincidencias = [
            key for key in drive_ids.keys()
            if normalizar_codigo(key).startswith(codigo)
        ]
        if coincidencias:
            encontrados.extend(coincidencias)
        else:
            no_encontrados.append(codigo)

    encontrados = sorted(list(set(encontrados)), key=lambda x: x.upper())

    st.session_state["encontrados"] = encontrados
    st.session_state["no_encontrados"] = no_encontrados

# ========================================
# 🧾 MOSTRAR RESULTADOS
# ========================================
if "encontrados" in st.session_state:
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    col1, col2 = st.columns(2)

    # --- Columna izquierda: encontrados ---
    with col1:
        st.markdown("<h5 style='font-size:15px;'>✅ Códigos encontrados</h5>", unsafe_allow_html=True)
        if encontrados:
            for key in encontrados:
                st.markdown(f"<div style='color:white; font-size:13px;'>{key}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:white; font-size:15px;'>No se encontraron códigos</div>", unsafe_allow_html=True)

    # --- Columna derecha: no encontrados ---
    with col2:
        st.markdown("<h5 style='font-size:15px;'>❌ Códigos no encontrados</h5>", unsafe_allow_html=True)
        if no_encontrados:
            for codigo in no_encontrados:
                st.markdown(f"<div style='color:white; font-size:13px;'>{codigo}</div>", unsafe_allow_html=True)

    # ========================================
    # 📦 BOTONES DE DESCARGA
    # ========================================
    if encontrados:
        colA, colB, colC = st.columns(3)

        with colA:
            if any(k.endswith("_1") for k in encontrados):
                buffer1 = generar_zip(encontrados, "1")
                st.download_button(
                    label="⬇️ Descargar IM1",
                    data=buffer1,
                    file_name="imagenes_IM1.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="btn_im1",
                )

        with colB:
            if any(k.endswith("_2") for k in encontrados):
                buffer2 = generar_zip(encontrados, "2")
                st.download_button(
                    label="⬇️ Descargar IM2",
                    data=buffer2,
                    file_name="imagenes_IM2.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="btn_im2",
                )

        with colC:
            buffer_all = generar_zip(encontrados)
            st.download_button(
                label="⬇️ Descargar todo",
                data=buffer_all,
                file_name="imagenes_todas.zip",
                mime="application/zip",
                use_container_width=True,
                key="btn_todo",
            )
