import streamlit as st
import pandas as pd

def render(supabase):
    st.subheader("📂 Directorio de Clientes")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### Nuevo Cliente")
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            nombre = st.text_input("Nombre de la Empresa / Cliente *")
            nit = st.text_input("NIT")
            telefono = st.text_input("Teléfono")
            submit_cliente = st.form_submit_button("Guardar Cliente")
            
            if submit_cliente:
                if nombre:
                    try:
                        data = {"nombre": nombre, "nit": nit, "telefono": telefono}
                        supabase.table("clientes").insert(data).execute()
                        st.success("Cliente guardado exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("El nombre es obligatorio.")

    with col2:
        st.markdown("#### Clientes Registrados")
        try:
            response = supabase.table("clientes").select("*").execute()
            if response.data:
                df_clientes = pd.DataFrame(response.data)
                df_clientes = df_clientes[["nombre", "nit", "telefono"]]
                df_clientes.columns = ["Nombre", "NIT", "Teléfono"]
                st.dataframe(df_clientes, use_container_width=True, hide_index=True)
            else:
                st.info("No hay clientes registrados aún.")
        except Exception as e:
            st.error(f"Error al cargar clientes: {e}")
