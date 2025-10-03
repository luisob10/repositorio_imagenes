import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
from PIL import Image

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "clave123"  # cámbiala a la tuya

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    clave = st.text_input("🔐 Ingresa la clave de acceso", type="password")
    if st.button("Entrar"):
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.rerun()  # 🔁 Redirige automáticamente a la siguiente pestaña
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
# 🌐 INTERFAZ PRINCIPAL
# ========================================
st.markdown("### 📥 Ingresar códigos")
st.write("Pega los códigos (separados por comas o saltos de línea):")

input_codigos = st.text_area("Códigos desde Excel", height=150, label_visibility="collapsed")

if st.button("Buscar"):
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
    else:
        codigos = [c.strip() for c in input_codigos.replace("\n", ",").split(",") if c.strip()]
        encontrados, no_encontrados = [], []

        # Descarga de imágenes para los encontrados
        buffer_zip = BytesIO()
        with ZipFile(buffer_zip, "w") as zipf:
            for codigo in codigos:
                if codigo in drive_ids:
                    img = obtener_imagen(drive_ids[codigo])
                    if img:
                        encontrados.append((codigo, img))
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="JPEG")
                        zipf.writestr(f"{codigo}.jpg", img_bytes.getvalue())
                    else:
                        no_encontrados.append(codigo)
                else:
                    no_encontrados.append(codigo)

        buffer_zip.seek(0)

        # ========================================
        # 📋 MOSTRAR RESULTADOS EN 2 COLUMNAS
        # ========================================
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ✅ Códigos encontrados")
            if encontrados:
                for codigo, img in encontrados:
                    with st.popover(codigo):
                        st.image(img, width=150)
            else:
                st.info("No se encontró ningún código válido.")

        with col2:
            st.markdown("#### ⚠️ Códigos no encontrados")
            if no_encontrados:
                for codigo in no_encontrados:
                    st.markdown(f"- {codigo}")
            else:
                st.info("Todos los códigos fueron encontrados.")

        # ========================================
        # 📦 BOTÓN DE DESCARGA DIRECTA
        # ========================================
        if encontrados:
            st.download_button(
                label="⬇️ Descargar todo (ZIP)",
                data=buffer_zip,
                file_name="imagenes_encontradas.zip",
                mime="application/zip"
            )
