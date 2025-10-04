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
            .code-box .preview img {
                width:350px !important;   /* 👈 tamaño fijo */
                max-width:350px !important;
                height:auto !important;
            }
            .code-box:hover .preview {
                display:block;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
