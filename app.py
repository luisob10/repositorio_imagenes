# ========================================
# 🧾 MOSTRAR RESULTADOS
# ========================================
if "encontrados" in st.session_state:
    encontrados = st.session_state["encontrados"]
    no_encontrados = st.session_state["no_encontrados"]

    # --- Crear dos columnas para resultados ---
    col_left, col_right = st.columns(2)

    # =========================
    # 📌 Columna IZQUIERDA: Encontrados
    # =========================
    with col_left:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### ✅ Códigos encontrados ({len(encontrados)})")
        with col2:
            if encontrados:
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
                        <img src="data:image/jpeg;base64,{img_base64}" width="250"/>
                    </div>
                </div>
                """

            st.markdown(html_codes, unsafe_allow_html=True)
        else:
            st.info("No se encontró ningún código válido.")

    # =========================
    # 📌 Columna DERECHA: No encontrados
    # =========================
    with col_right:
        if no_encontrados:
            st.markdown(f"#### ❌ Códigos no encontrados ({len(no_encontrados)})")
            for codigo in no_encontrados:
                st.markdown(
                    f"<span style='margin:5px; padding:3px 6px; border:1px solid #aaa; border-radius:5px;'>{codigo}</span>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No hubo códigos no encontrados.")
