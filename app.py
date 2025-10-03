import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import base64

# ========================================
# 🔐 CONFIGURACIÓN DE LOGIN
# ========================================
PASSWORD = "123"  # cámbiala a la tuya

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# --- (1) Ingresar también con tecla ENTER ---
if not st.session_state["autenticado"]:
    clave = st.text_input("🔐 Ingresa la clave de acceso", type="password")
    # Si presiona Enter o el botón
    if clave and (st.session_state.get("clave_enter") or st.button("Entrar")):
        if clave == PASSWORD:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Clave incorrecta")
    # Detectar Enter
    st.session_state["clave_enter"] = clave != ""
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

# --- (2) Eliminar texto de ayuda y (3) duplicar tamaño de caja ---
input_codigos = st.text_area(
    "Códigos desde Excel", 
    height=300,  # tamaño al doble
    label_visibility="collapsed"
)

# Variable para controlar resaltado del código faltante
if "resaltado" not in st.session_state:
    st.session_state["resaltado"] = ""

# ========================================
# 🔍 BUSCAR CÓDIGOS
# ========================================
if st.button("Buscar"):
    if not input_codigos.strip():
        st.warning("Por favor ingresa al menos un código.")
    else:
        codigos = [c.strip() for c in input_codigos.replace("\n", ",").split(",") if c.strip()]
        encontrados, no_encontrados = [], []

        for codigo in codigos:
            if codigo in drive_ids:
                img = obtener_imagen(drive_ids[codigo])
                if img:
                    encontrados.append((codigo, img))
                else:
                    no_encontrados.append(codigo)
            else:
                no_encontrados.append(codigo)

        # ========================================
        # 📋 MOSTRAR RESULTADOS EN 2 COLUMNAS
        # ========================================
        col1, col2 = st.columns(2)

        # --- (5) Mostrar imagen al pasar el cursor ---
        with col1:
            st.markdown("#### ✅ Códigos encontrados")
            if encontrados:
                for codigo, img in encontrados:
                    buffered = BytesIO()
                    img.save(buffered, format="JPEG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()
                    st.markdown(
                        f"""
                        <div style="position:relative; display:inline-block; margin:5px;">
                            <span style="cursor:pointer; color:#0066cc;">{codigo}</span>
                            <div style="position:absolute; top:20px; left:0; display:none; z-index:100; border:1px solid #ccc; background:white;">
                                <img src="data:image/jpeg;base64,{img_base64}" width="200"/>
                            </div>
                        </div>
                        <script>
                        const container = document.currentScript.previousElementSibling;
                        const imgDiv = container.querySelector('div');
                        container.onmouseover = () => imgDiv.style.display='block';
                        container.onmouseout = () => imgDiv.style.display='none';
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No se encontró ningún código válido.")

        # --- (4) Click en código no encontrado para resaltarlo ---
        with col2:
            st.markdown("#### ⚠️ Códigos no encontrados")
            if no_encontrados:
                for codigo in no_encontrados:
                    st.markdown(
                        f"""
                        <span 
                            style='cursor:pointer; color:#cc0000; text-decoration:underline;'
                            onClick="window.parent.postMessage({{'codigo_faltante':'{codigo}'}}, '*')"
                        >{codigo}</span><br>
                        """, 
                        unsafe_allow_html=True
                    )
            else:
                st.info("Todos los códigos fueron encontrados.")

        # Script para resaltar en caja de texto (JS + Streamlit event)
        st.markdown("""
        <script>
        window.addEventListener('message', (event) => {
            const data = event.data;
            if (data.codigo_faltante) {
                const textarea = parent.document.querySelector('textarea');
                if (textarea) {
                    const text = textarea.value;
                    const start = text.indexOf(data.codigo_faltante);
                    if (start !== -1) {
                        textarea.focus();
                        textarea.setSelectionRange(start, start + data.codigo_faltante.length);
                    }
                }
            }
        });
        </script>
        """, unsafe_allow_html=True)

        # ========================================
        # 💾 DESCARGA DIRECTA DE IMÁGENES
        # ========================================
        if encontrados:
            st.markdown("#### ⬇️ Descargar todo")

            for codigo, img in encontrados:
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                btn = st.download_button(
                    label=f"Descargar {codigo}.jpg",
                    data=buffered.getvalue(),
                    file_name=f"{codigo}.jpg",
                    mime="image/jpeg"
                )
