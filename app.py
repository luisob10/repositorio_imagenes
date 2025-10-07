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
# 🔧 NORMALIZAR CÓDIGOS
# ========================================
def normalizar_codigo(codigo):
    """Quita espacios, extensión .jpg y convierte a minúsculas para comparación."""
    return codigo.strip().replace(".jpg", "").replace(".JPG", "").lower()

# ========================================
# 🌐 INTERFAZ PRINCIPAL
# ========================================
st.markdown("### 📥 Ingresar códigos")

input_codigos = st.text_area(
    "Códigos desde Excel",
    height=300,
    label_visibility="collapsed"
)

# ========================================
# 🔍 BUSCAR CÓDIGOS NORMALIZADOS
# ========================================
if st.button("Buscar"):
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
    else:
        codigos = [c.strip() for c in input_codigos.replace("\n", ",").split(",") if c.strip()]
        encontrados = []
        no_encontrados = []

        for codigo in codigos:
            cod_norm = normalizar_codigo(codigo)
            encontrado = None

            # Buscar en el CSV normalizando también
            for key in drive_ids:
                if normalizar_codigo(key) == cod_norm:
                    encontrado = key
                    break

            if encontrado:
                img = obtener_imagen(drive_ids[encontrado])
                if img:
                    encontrados.append((encontrado, img))
                else:
                    no_encontrados.append(codigo)
            else:
                no_encontrados.append(codigo)

        st.session_state["encontrados"] = encontrados
        st.session_state["no_encontrados"] = no_encontrados

# ========================================
# 🧾 MOSTRAR RESULTADOS
# ========================================
if "encontrados" in st.session_state:
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    # --- Sección Encontrados con botones ---
    if encontrados:
        col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1])

        with col1:
            st.markdown(f"#### ✅ Códigos encontrados ({len(encontrados)})")

        # 📦 Descargar todo
        with col2:
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

        # ⬇️ IM1
        with col3:
            zip_buffer_im1 = BytesIO()
            with ZipFile(zip_buffer_im1, "w") as zip_file:
                for codigo, img in encontrados:
                    if codigo.endswith("_1"):
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="JPEG")
                        zip_file.writestr(f"{codigo}.jpg", img_bytes.getvalue())
            zip_buffer_im1.seek(0)
            st.download_button(
                label="⬇️ IM1",
                data=zip_buffer_im1,
                file_name="imagenes_IM1.zip",
                mime="application/zip",
                key="descargar_im1"
            )

        # ⬇️ IM2
        with col4:
            zip_buffer_im2 = BytesIO()
            with ZipFile(zip_buffer_im2, "w") as zip_file:
                for codigo, img in encontrados:
                    if codigo.endswith("_2"):
                        img_bytes = BytesIO()
                        img.save(img_bytes, format="JPEG")
                        zip_file.writestr(f"{codigo}.jpg", img_bytes.getvalue())
            zip_buffer_im2.seek(0)
            st.download_button(
                label="⬇️ IM2",
                data=zip_buffer_im2,
                file_name="imagenes_IM2.zip",
                mime="application/zip",
                key="descargar_im2"
            )

    # --- Mostrar códigos encontrados con preview ---
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

        html_codes = ""
        for codigo, img in encontrados:
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            html_codes += f"""
            <div class="code-box">
                {codigo}
                <div class="preview">
                    <img src="data:image/jpeg;base64,{img_base64}" width="350"/>
                </div>
            </div>
            """

        st.markdown(html_codes, unsafe_allow_html=True)
    else:
        st.info("No se encontró ningún código válido.")

    # --- Mostrar códigos no encontrados ---
    if no_encontrados:
        st.markdown(f"#### ❌ Códigos no encontrados ({len(no_encontrados)})")
        for codigo in no_encontrados:
            st.markdown(
                f"<span style='margin:5px; padding:3px 6px; border:1px solid #aaa; border-radius:5px; color:white;'>{codigo}</span>",
                unsafe_allow_html=True
            )
