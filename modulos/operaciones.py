import streamlit as st

def render(tipo_cambio, supabase):
    st.subheader("⚙️ Control de Operaciones y Embarques")
    st.info(f"Tipo de cambio actual: Q. {tipo_cambio}")
    
    tab_registro, tab_seguimiento = st.tabs(["📦 Nuevo Embarque", "📍 Seguimiento"])
    
    with tab_registro:
        with st.form("form_operaciones", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                bl_number = st.text_input("Número de BL / Booking")
                naviera = st.text_input("Naviera / Co-loader")
                origen = st.text_input("Puerto de Origen")
            with col2:
                contenedor = st.text_input("Número de Contenedor")
                eta = st.date_input("Fecha Estimada de Arribo (ETA)")
                destino = st.text_input("Puerto de Destino")
                
            if st.form_submit_button("Registrar Embarque"):
                # Aquí puedes agregar luego la tabla "embarques" en Supabase
                st.success(f"Embarque {bl_number} registrado (Función en desarrollo).")
                
    with tab_seguimiento:
        st.write("Aquí se mostrará el listado de contenedores en tránsito y sus demoras.")
