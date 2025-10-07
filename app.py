import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
from PIL import Image
import base64
import re

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "123"  # cámbiala a la tuya

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    # --- Login sin título ---
    clave = st.text_input("🔑 Ingresa la clave de acceso", type="password", key="clave")

    # Permitir Enter además del botón
    login = st.button("Entrar") or (st.session_state.clave == PASSWORD and st.session_state.get("enter_pressed", False))

    if login:
        if st.session_state.clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.experimental_rerun()
        else:
            st.error("❌ Clave incorrecta")

    # Detectar Enter correctamente
    st.session_state["enter_pressed"] = False
    st.markdown(
        """
        <script>
        const input = window.parent.document.querySelector('input[type="password"]');
        if (input) {
            input.addEventListener('keydown', e => {
                if (e.key === 'Enter') {
                    window.parent.postMessage({ type: 'enter_pressed' }, '*');
                }
            });
        }
        </script>
        """,
        unsafe_allow_html=True,
    )

    st.stop()

# ========================================
# 📂 CARGAR CSV DE IMÁGENES
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
    return re.sub(r"[^A-Za-z0-9\\-]", "", str(c)).strip().upper()

def descargar_zip(filtro):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for key, file_id in drive_ids.items():
            if key.endswith(f"_{filtro}"):
                url = f"https://drive.google.com/uc?id={file_id}"
                try:
                    resp = requests.get(url)
                    zip_file.writestr(f"{key}.jpg", resp.content)
                except:
                    pass
    buffer.seek(0)
    return buffer

# ========================================
# 🧠 INTERFAZ PRINCIPAL
# ========================================
input_codigos = st.text_area("", height=200, placeholder="Pega o escribe los códigos aquí...")

buscar = st.button("🔍 Buscar")

# Botones IM1 e IM2 (debajo del botón Buscar)
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("⬇️ IM1 (Descargar terminación _1)"):
        zip_data = descargar_zip("1")
        st.download_button("Descargar IM1.zip", data=zip_data, file_name="imagenes_IM1.zip", mime="application/zip")
with col_btn2:
    if st.button("⬇️ IM2 (Descargar terminación _2)"):
        zip_data = descargar_zip("2")
        st.download_button("Descargar IM2.zip", data=zip_data, file_name="imagenes_IM2.zip", mime="application/zip")

# ========================================
# 🔍 BÚSQUEDA DE CÓDIGOS
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

    # ========================================
    # 📋 RESULTADOS EN DOS COLUMNAS
    # ========================================
    col1, col2 = st.columns(2)

    # ----- Códigos encontrados -----
    with col1:
        st.markdown("<h5 style='font-size:14px;'>✅ Códigos encontrados</h5>", unsafe_allow_html=True)
        if encontrados:
            st.markdown(
                """
                <style>
                .code-box {
                    display:inline-block;
                    position:relative;
                    margin:5px;
                    padding:3px 6px;
                    border:1px solid #4CAF50;
                    border-radius:5px;
                    cursor:pointer;
                    font-size:12px;
                    color:white;
                }
                .code-box .preview {
                    display:none;
                    position:absolute;
                    top:25px;
                    left:0;
                    z-index:100;
                    border:1px solid #ccc;
                    background:white;
                    padding:2px;
                }
                .code-box:hover .preview {
                    display:block;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            html_codes = ""
            for key in encontrados:
                file_id = drive_ids[key]
                url = f"https://drive.google.com/uc?id={file_id}"
                html_codes += f"""
                <div class="code-box">{key}
                    <div class="preview">
                        <img src="{url}" width="200"/>
                    </div>
                </div>
                """
            st.markdown(html_codes, unsafe_allow_html=True)
        else:
            st.info("No se encontró ningún código válido.")

    # ----- Códigos no encontrados -----
    with col2:
        st.markdown("<h5 style='font-size:14px;'>❌ Códigos no encontrados</h5>", unsafe_allow_html=True)
        if no_encontrados:
            for codigo in no_encontrados:
                st.markdown(
                    f"<span style='color:white; font-size:12px;'>{codigo}</span>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Todos los códigos fueron encontrados ✅")
