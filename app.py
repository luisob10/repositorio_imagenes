import streamlit as st
import pandas as pd
import time
import re
from io import BytesIO
from zipfile import ZipFile

# ======================
# CONFIGURACIÓN INICIAL
# ======================
st.set_page_config(page_title="Buscador de Imágenes", layout="centered")

# Simulación de base de datos
df = pd.DataFrame({
    "codigo": [f"COD{i}_{j}" for i in range(1, 201) for j in range(1, 5)],
    "id": [f"ID{i}_{j}" for i in range(1, 201) for j in range(1, 5)]
})
drive_ids = dict(zip(df["codigo"], df["id"]))

# ======================
# FUNCIONES AUXILIARES
# ======================
def normalizar_codigo(c):
    return re.sub(r"[^A-Za-z0-9\-_]", "", str(c)).strip().upper()

def generar_zip(codigos):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipf:
        for codigo in codigos:
            zipf.writestr(f"{codigo}.txt", f"Archivo simulado para {codigo}")
    buffer.seek(0)
    return buffer

# ======================
# ESTADO DE SESIÓN
# ======================
if "progreso" not in st.session_state:
    st.session_state.progreso = 0
if "buscando" not in st.session_state:
    st.session_state.buscando = False
if "encontrados" not in st.session_state:
    st.session_state.encontrados = []
if "no_encontrados" not in st.session_state:
    st.session_state.no_encontrados = []

# ======================
# INTERFAZ
# ======================
st.title("🔍 Buscador de Imágenes con Progreso en Vivo")

input_codigos = st.text_area("Pega tus códigos aquí:", height=150)

# Barra de progreso global (siempre visible)
progress_bar = st.progress(st.session_state.progreso)
progress_text = st.empty()

# ======================
# FUNCIÓN DE BÚSQUEDA
# ======================
def buscar_codigos(codigos):
    encontrados, no_encontrados = [], []
    total = len(codigos)
    for i, codigo in enumerate(codigos):
        codigo_norm = normalizar_codigo(codigo)
        matches = [k for k in drive_ids.keys() if normalizar_codigo(k).startswith(codigo_norm)]
        if matches:
            encontrados.extend(matches)
        else:
            no_encontrados.append(codigo)
        # Actualizar progreso
        st.session_state.progreso = int(((i + 1) / total) * 100)
        progress_bar.progress(st.session_state.progreso)
        progress_text.markdown(f"**Buscando códigos... {st.session_state.progreso}%**")
        time.sleep(0.05)  # 👈 permite que la interfaz actualice
    return encontrados, no_encontrados

# ======================
# BOTÓN BUSCAR
# ======================
if st.button("Buscar"):
    if not input_codigos.strip():
        st.warning("⚠️ Ingresa al menos un código antes de buscar.")
        st.stop()

    st.session_state.buscando = True
    st.session_state.progreso = 0
    progress_bar.progress(0)
    progress_text.markdown("**Buscando códigos... 0%**")

    codigos = [c.strip() for c in re.split(r"[,\n]+", input_codigos) if c.strip()]
    encontrados, no_encontrados = buscar_codigos(codigos)

    st.session_state.encontrados = encontrados
    st.session_state.no_encontrados = no_encontrados
    st.session_state.buscando = False

    st.success("✅ Búsqueda completada al 100%")

# ======================
# RESULTADOS Y DESCARGAS
# ======================
if st.session_state.encontrados:
    st.subheader("📦 Descargas disponibles")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        im1 = [c for c in st.session_state.encontrados if c.endswith("_1")]
        if im1:
            st.download_button("⬇️ IM1", generar_zip(im1), "IM1.zip", mime="application/zip")

    with col2:
        im2 = [c for c in st.session_state.encontrados if c.endswith("_2")]
        if im2:
            st.download_button("⬇️ IM2", generar_zip(im2), "IM2.zip", mime="application/zip")

    with col3:
        im3 = [c for c in st.session_state.encontrados if c.endswith("_3")]
        if im3:
            st.download_button("⬇️ IM3", generar_zip(im3), "IM3.zip", mime="application/zip")

    with col4:
        im4 = [c for c in st.session_state.encontrados if c.endswith("_4")]
        if im4:
            st.download_button("⬇️ IM4", generar_zip(im4), "IM4.zip", mime="application/zip")

    with col5:
        st.download_button("⬇️ Descargar Todo", generar_zip(st.session_state.encontrados),
                           "Todo.zip", mime="application/zip")

if st.session_state.no_encontrados:
    st.error(f"❌ {len(st.session_state.no_encontrados)} códigos no encontrados.")
