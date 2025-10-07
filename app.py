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
    st.title("🔐 Ingreso")
    clave = st.text_input("Ingrese la clave de acceso", type="password", key="clave")

    if st.button("Entrar") or (clave and st.session_state.get("enter_pressed", False)):
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.experimental_rerun()
        else:
            st.error("Clave incorrecta")

    # Permitir ingresar con ENTER
    st.session_state["enter_pressed"] = st.session_state.get("enter_pressed", False)
    if st.session_state["enter_pressed"]:
        st.session_state["enter_pressed"] = False
else:
    # ========================================
    # 📂 CARGA DEL CSV
    # ========================================
    try:
        df = pd.read_csv("imagenes.csv")
        drive_ids = dict(zip(df["codigo"], df["id"]))
    except Exception as e:
        st.error(f"No se pudo cargar 'imagenes.csv': {e}")
        st.stop()

    # ========================================
    # 🎯 FUNCIÓN PARA NORMALIZAR CÓDIGOS
    # ========================================
    def normalizar_codigo(c):
        return re.sub(r"[^A-Za-z0-9\-]", "", str(c)).strip().upper()

    # ========================================
    # 🧩 INTERFAZ PRINCIPAL
    # ========================================
    st.title("📸 Ingresar Códigos")
    codigos_usuario = st.text_area(
        "",
        height=200,
        placeholder="Escriba o pegue los códigos aquí...",
    )

    if st.button("Buscar"):
        if not codigos_usuario.strip():
            st.warning("Ingrese al menos un código.")
            st.stop()

        codigos = [normalizar_codigo(c) for c in re.split(r"[,\n]+", codigos_usuario) if c.strip()]
        encontrados = {}
        no_encontrados = []

        for codigo in codigos:
            coincidencias = [
                key for key in drive_ids.keys()
                if normalizar_codigo(key).startswith(codigo)
            ]
            if coincidencias:
                for c in coincidencias:
                    encontrados[c] = drive_ids[c]
            else:
                no_encontrados.append(codigo)

        # ========================================
        # 📋 RESULTADOS
        # ========================================
        if encontrados:
            st.subheader("✅ Códigos encontrados")
            for codigo, file_id in encontrados.items():
                img_url = f"https://drive.google.com/uc?id={file_id}"
                st.markdown(
                    f"<span style='color:white; cursor:pointer; text-decoration:underline;' "
                    f"onClick=\"window.parent.postMessage({{'codigo_encontrado':'{codigo}'}}, '*')\">{codigo}</span>",
                    unsafe_allow_html=True,
                )
                try:
                    image = Image.open(BytesIO(requests.get(img_url).content))
                    st.image(image, width=250)
                except Exception:
                    st.warning(f"No se pudo cargar la imagen para {codigo}")

            # ========================================
            # 📦 DESCARGAR ZIP
            # ========================================
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                for codigo, file_id in encontrados.items():
                    img_url = f"https://drive.google.com/uc?id={file_id}"
                    try:
                        response = requests.get(img_url)
                        zip_file.writestr(f"{codigo}.jpg", response.content)
                    except Exception:
                        pass
            zip_buffer.seek(0)

            st.download_button(
                label="⬇️ Descargar todo (ZIP)",
                data=zip_buffer,
                file_name="imagenes_encontradas.zip",
                mime="application/zip",
            )

        if no_encontrados:
            st.subheader("❌ Códigos no encontrados")
            for codigo in no_encontrados:
                st.markdown(
                    f"<span style='color:white; cursor:pointer; text-decoration:underline;' "
                    f"onClick=\"window.parent.postMessage({{'codigo_faltante':'{codigo}'}}, '*')\">{codigo}</span>",
                    unsafe_allow_html=True,
                )

        if not encontrados and not no_encontrados:
            st.warning("No se encontró ningún código válido.")
