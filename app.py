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
    clave = st.text_input("Ingrese la clave de acceso", type="password")

    if st.button("Entrar") or (clave and st.session_state.get("enter_pressed", False)):
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.experimental_rerun()
        else:
            st.error("Clave incorrecta")

    st.session_state["enter_pressed"] = st.session_state.get("enter_pressed", False)
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
    codigos_usuario = st.text_area("", height=200, placeholder="Escriba o pegue los códigos aquí...")

    if st.button("Buscar"):
        if not codigos_usuario.strip():
            st.warning("Ingrese al menos un código.")
            st.stop()

        codigos = [normalizar_codigo(c) for c in re.split(r"[,\n]+", codigos_usuario) if c.strip()]
        encontrados = {}
        no_encontrados = []

        # Buscar coincidencias parciales
        for codigo in codigos:
            coincidencias = [
                key for key in drive_ids.keys()
                if normalizar_codigo(key).startswith(codigo)
            ]
            if coincidencias:
                encontrados[codigo] = coincidencias
            else:
                no_encontrados.append(codigo)

        # ========================================
        # 📋 RESULTADOS EN DOS COLUMNAS
        # ========================================
        col1, col2 = st.columns(2)

        # ---------------- CÓDIGOS ENCONTRADOS ----------------
        with col1:
            st.subheader("✅ Códigos encontrados")

            if encontrados:
                for base_codigo, lista_coincidencias in encontrados.items():
                    st.markdown(f"**{base_codigo}**")

                    # Mostrar botones IM1, IM2, ...
                    botones = ""
                    for i, key in enumerate(lista_coincidencias, start=1):
                        file_id = drive_ids[key]
                        img_url = f"https://drive.google.com/uc?id={file_id}"
                        botones += f"""
                        <a href="{img_url}" target="_blank" 
                           style="background-color:#1E88E5; color:white; padding:6px 10px; 
                                  border-radius:8px; text-decoration:none; margin-right:5px;"
                           onmouseover="this.nextElementSibling.style.display='block'"
                           onmouseout="this.nextElementSibling.style.display='none'">
                           IM{i}
                        </a>
                        <div style="display:none; position:absolute; z-index:999; background:#000000dd; 
                                    padding:4px; border-radius:8px;">
                            <img src="{img_url}" style="width:180px; border-radius:6px;">
                        </div>
                        """
                    st.markdown(botones, unsafe_allow_html=True)
                    st.markdown("<hr>", unsafe_allow_html=True)
            else:
                st.info("No se encontró ningún código válido.")

        # ---------------- CÓDIGOS NO ENCONTRADOS ----------------
        with col2:
            st.subheader("❌ Códigos no encontrados")
            if no_encontrados:
                for codigo in no_encontrados:
                    st.markdown(
                        f"<span style='color:white; text-decoration:underline;'>{codigo}</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Todos los códigos fueron encontrados ✅")

        # ========================================
        # 📦 DESCARGAR ZIP
        # ========================================
        if encontrados:
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                for _, lista_coincidencias in encontrados.items():
                    for key in lista_coincidencias:
                        file_id = drive_ids[key]
                        img_url = f"https://drive.google.com/uc?id={file_id}"
                        try:
                            response = requests.get(img_url)
                            zip_file.writestr(f"{key}.jpg", response.content)
                        except Exception:
                            pass
            zip_buffer.seek(0)
            st.download_button(
                label="⬇️ Descargar todo (ZIP)",
                data=zip_buffer,
                file_name="imagenes_encontradas.zip",
                mime="application/zip",
            )
