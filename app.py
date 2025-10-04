import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import base64
from zipfile import ZipFile

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "123"  # cámbiala a la tuya

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    with st.form("login_form"):
        clave = st.text_input("🔐 Ingresa la clave de acceso", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.rerun()
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
# 🌐 INTERFAZ PRINCIPAL (50% pantalla)
# ========================================
st.markdown(
    """
    <style>
    .main-container {
        width: 50vw !important;
        margin: auto; /* Centrado */
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.container():
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)

    # 3 columnas → 10% / 20% / 20%
    col_input, col_encontrados, col_noencontrados = st.columns([10, 20, 20])

    # =====================
    # 📥 Columna Ingreso
    # =====================
    with col_input:
        st.markdown("### 📥 Ingresar códigos")
        input_codigos = st.text_area(
            "Códigos desde Excel", 
            height=600,  
            label_visibility="collapsed"
        )

        if st.button("Buscar"):
            if not input_codigos.strip():
                st.warning("Por favor ingresa al menos un código.")
            else:
                codigos = [c.strip() for c in input_codigos.replace("\n", ",").split(",") if c.strip()]
                encontrados = []
                no_encontrados = []

                for codigo in codigos:
                    if codigo in drive_ids:
                        img = obtener_imagen(drive_ids[codigo])
                        if img:
                            encontrados.append((codigo, img))
                        else:
                            no_encontrados.append(codigo)
                    else:
                        no_encontrados.append(codigo)

                st.session_state["encontrados"] = encontrados
                st.session_state["no_encontrados"] = no_encontrados

    # =====================
    # ✅ Columna Encontrados
    # =====================
    with col_encontrados:
        if "encontrados" in st.session_state:
            encontrados = st.session_state["encontrados"]

            st.markdown(f"#### ✅ Encontrados ({len(encontrados)})")

            if encontrados:
                # Botón descargar ZIP
                zip_buffer = BytesIO()
                with ZipFile(zip_buffer, "w") as zip_file:
                    for codigo, img in encontrados:
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="JPEG")
                        zip_file.writestr(f"{codigo}.jpg", img_bytes.getvalue())
                zip_buffer.seek(0)
                st.download_button(
                    label="📦 Descargar todo",
                    data=zip_buffer,
                    file_name="imagenes_encontradas.zip",
                    mime="application/zip",
                    key="descargar_zip"
                )

                # Mostrar previews
                for codigo, img in encontrados:
                    buffered = BytesIO()
                    img.save(buffered, format="JPEG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()

                    st.markdown(
                        f"<div style='margin:5px; border:1px solid #4CAF50; padding:3px; border-radius:5px;'>{codigo}</div>",
                        unsafe_allow_html=True
                    )
                    st.image(img, width=180)

            else:
                st.info("No se encontró ningún código válido.")

    # =====================
    # ❌ Columna No encontrados
    # =====================
    with col_noencontrados:
        if "no_encontrados" in st.session_state:
            no_encontrados = st.session_state["no_encontrados"]
            st.markdown(f"#### ❌ No encontrados ({len(no_encontrados)})")
            for codigo in no_encontrados:
                st.markdown(
                    f"<div style='margin:5px; border:1px solid #aaa; padding:3px; border-radius:5px;'>{codigo}</div>",
                    unsafe_allow_html=True
                )

    st.markdown("</div>", unsafe_allow_html=True)
