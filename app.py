import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
import re

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "123"  # cámbiala a la tuya

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("")  # eliminar título grande
    clave = st.text_input("🔑 Ingresa la clave de acceso", type="password", key="clave_input")

    # Detectar Enter automáticamente
    if "enter_pressed" not in st.session_state:
        st.session_state["enter_pressed"] = False

    if st.session_state["enter_pressed"] or st.button("Entrar"):
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")

    # Verificar si se presionó Enter (sin JS)
    if clave and st.session_state.get("last_clave") != clave:
        st.session_state["enter_pressed"] = True
        st.session_state["last_clave"] = clave
    else:
        st.session_state["enter_pressed"] = False

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

def descargar_zip_por_sufijo(sufijo, encontrados):
    """Descarga todas las imágenes que terminan en _{sufijo} y estén en los encontrados"""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for key in encontrados:
            if key.endswith(f"_{sufijo}"):
                file_id = drive_ids[key]
                url = f"https://drive.google.com/uc?id={file_id}"
                try:
                    resp = requests.get(url)
                    zip_file.writestr(f"{key}.jpg", resp.content)
                except Exception:
                    pass
    buffer.seek(0)
    st.download_button(
        label=f"⬇️ Descargar IM{sufijo}",
        data=buffer,
        file_name=f"imagenes_IM{sufijo}.zip",
        mime="application/zip",
        key=f"dl_im{sufijo}"
    )

def descargar_todo(encontrados):
    """Descarga todas las imágenes encontradas"""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for key in encontrados:
            file_id = drive_ids[key]
            url = f"https://drive.google.com/uc?id={file_id}"
            try:
                resp = requests.get(url)
                zip_file.writestr(f"{key}.jpg", resp.content)
            except Exception:
                pass
    buffer.seek(0)
    st.download_button(
        label="⬇️ Descargar todo",
        data=buffer,
        file_name="imagenes_todas.zip",
        mime="application/zip",
        key="dl_todo"
    )

# ========================================
# 🧠 INTERFAZ PRINCIPAL
# ========================================
st.markdown("<h6 style='margin-bottom:0;'>Ingresar códigos</h6>", unsafe_allow_html=True)
input_codigos = st.text_area("", height=200, placeholder="Pega o escribe los códigos aquí...")

buscar = st.button("🔍 Buscar")

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

    # --- Estilo general ---
    st.markdown(
        """
        <style>
        .code-box {
            display:inline-block;
            position:relative;
            margin:4px;
            padding:4px 8px;
            border:1px solid #4CAF50;
            border-radius:5px;
            cursor:pointer;
            font-size:13px;
            color:white;
            background-color:#333;
        }
        .code-box .preview {
            display:none;
            position:absolute;
            top:28px;
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

    # --- Códigos encontrados ---
    with col1:
        st.markdown("<h5 style='font-size:15px;'>✅ Códigos encontrados</h5>", unsafe_allow_html=True)
        if encontrados:
            html_codes = ""
            for key in encontrados:
                file_id = drive_ids[key]
                url = f"https://drive.google.com/uc?id={file_id}"
                html_codes += f"""
                <div class="code-box">{key}
                    <div class="preview">
                        <img src="{url}" width="180"/>
                    </div>
                </div>
                """
            st.markdown(html_codes, unsafe_allow_html=True)
        else:
            st.info("No se encontró ningún código válido.")

    # --- Códigos no encontrados ---
    with col2:
        st.markdown("<h5 style='font-size:15px;'>❌ Códigos no encontrados</h5>", unsafe_allow_html=True)
        if no_encontrados:
            for codigo in no_encontrados:
                st.markdown(
                    f"<span style='color:white; font-size:13px;'>{codigo}</span>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Todos los códigos fueron encontrados ✅")

    # ========================================
    # 📦 BOTONES DE DESCARGA (SOLO SI HAY ENCONTRADOS)
    # ========================================
    if encontrados:
        st.markdown("---")
        st.markdown("### 📥 Descargas disponibles")

        if any(k.endswith("_1") for k in encontrados):
            descargar_zip_por_sufijo("1", encontrados)
        if any(k.endswith("_2") for k in encontrados):
            descargar_zip_por_sufijo("2", encontrados)

        descargar_todo(encontrados)
