# =====================
# 📥 Columna Ingreso
# =====================
with col_input:
    st.markdown("### 📥 Ingresar códigos")

    # --- Colocamos input + botón en horizontal ---
    col_txt, col_btn = st.columns([4, 1])  # 4/5 ancho para el input y 1/5 para el botón

    with col_txt:
        input_codigos = st.text_area(
            "Códigos desde Excel", 
            height=100,  # más pequeño para horizontal
            label_visibility="collapsed"
        )

    with col_btn:
        buscar = st.button("Buscar")

    if buscar:
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
