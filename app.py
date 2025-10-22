import streamlit as st
import pandas as pd
import re
import time
from io import BytesIO
from zipfile import ZipFile

# ======================
# CONFIGURACIÓN INICIAL
# ======================
st.set_page_config(page_title="Buscador de Imágenes", layout="centered")

# Simulación de base de datos de Drive
df = pd.DataFrame({
    "codigo": [f"COD{i}_{j}" for i in range(1, 1001) for j in range(1, 5)],
    "id": [f"ID{i}_{j}" for i in range(1, 1001) for j in range(1, 5)]
})
drive_ids = dict(zip(df["codigo"], df["id"]))

# ======================
# FUNCIONES AUXILIARES
# ======================
def normalizar_codigo(codigo):
    """Limpia el código de caracteres especiales."""
    return re.sub(r"[^A-Za-z0-9\-_]", "", str(codigo)).strip().upper()

def generar_zip(lista_codigos):
    """Genera un ZIP con archivos simulados según los códigos encontrados."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipf:
        for codigo in lista_codigos:
            zipf.writestr(f"{codigo}.txt", f"Archivo simulado para {codigo}")
    buffer.seek(0)
    return buffer

def buscar_codigos(codigos):
    """Simula la búsqueda de códigos y actualiza el progreso visualmente."""
    encontrados = []
    no_encontrados = []
    total = len(codigos)

    progress_bar = st.progress(0)
    progress_text = st.empty()

    for i, codigo in enumerate(codigos):
        codigo_norm = normalizar_codigo(codigo)
        matches = [k for k in drive_ids.keys() if normalizar_codigo(k).startswith(codigo_norm)]

        if matches:
            encontrados.extend(matches)
        else:
            no_encontrados.append(codigo)

        progreso = int(((i + 1) / total) * 100)
        progress_bar.progress(progreso)
        progress_text.markdown(f"**Buscando códigos... {progreso}%**")
        time.sleep(0.01)  # 👈 Permite actualizar visualmente la interfaz

    progress_text.markdown("✅ **Búsqueda completada (100%)**")
    return encontrados, no_encontrados


# ======================
# INTERFAZ PRINCIPAL
# ======================
st.title("🔍 Buscador de Imágenes con Progreso en Vivo")

st.markdown("""
Pega una lista de códigos (uno por línea o separados por comas).  
Mientras se realiza la búsqueda, verás el porcentaje de avance en tiempo real.
""")

input_codigos = st.text_area("📋 Ingresa los códigos:", height=180)

# Variables de sesión para mantener resultados
if "encontrados" not in st.session_state:
    st.session_state.encontrados = []
if "no_encontrados" not in st.session_state:
    st.session_state.no_encontrados = []

# ======================
# BOTÓN BUSCAR
# ======================
if st.button("🔎 Buscar"):
    if not input_codigos.strip():
        st.warning("⚠️ Ingresa al menos un código antes de buscar.")
        st.stop()

    st.info("⏳ Iniciando búsqueda, por favor espera...")
    codigos = [c.strip() for c in re.split(r"[,\n]+", input_codigos) if c.strip()]

    encontrados, no_encontrados = buscar_codigos(codigos)

    st.session_state.encontrados = encontrados
    st.session_state.no_encontrados = no_encontrados

    st.success("✅ Búsqueda completada correctamente.")


# ======================
# RESULTADOS Y DESCARGAS
# ======================
if st.session_state.encontrados:
    st.subheader("📦 Resultados encontrados")
    st.write(f"Se encontraron **{len(st.session_state.encontrados)}** coincidencias.")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        im1 = [c for c in st.session_state.encontrados if c.endswith("_1")]
        if im1:
            st.download_button(
                "⬇️ IM1",
                generar_zip(im1),
                "IM1.zip",
                mime="application/zip"
            )

    with col2:
        im2 = [c for c in st.session_state.encontrados if c.endswith("_2")]
        if im2:
            st.download_button(
                "⬇️ IM2",
                generar_zip(im2),
                "IM2.zip",
                mime="application/zip"
            )

    with col3:
        im3 = [c for c in st.session_state.encontrados if c.endswith("_3")]
        if im3:
            st.download_button(
                "⬇️ IM3",
                generar_zip(im3),
                "IM3.zip",
                mime="application/zip"
            )

    with col4:
        im4 = [c for c in st.session_state.encontrados if c.endswith("_4")]
        if im4:
            st.download_button(
                "⬇️ IM4",
                generar_zip(im4),
                "IM4.zip",
                mime="application/zip"
            )

    with col5:
        st.download_button(
            "⬇️ Descargar Todo",
            generar_zip(st.session_state.encontrados),
            "Todo.zip",
            mime="application/zip"
        )

# ======================
# CÓDIGOS NO ENCONTRADOS
# ======================
if st.session_state.no_encontrados:
    st.subheader("❌ Códigos no encontrados")
    st.write(f"No se encontraron {len(st.session_state.no_encontrados)} códigos.")
    with st.expander("Ver lista"):
        st.text("\n".join(st.session_state.no_encontrados))
