import streamlit as st
import pandas as pd

def render(tipo_cambio, supabase):
    st.subheader("📦 Registro de Embarques (BL / Booking)")
    st.write("Asigna los embarques a tus clientes para tener el historial antes de facturarles.")
    
    # Obtener clientes para el selector
    try:
        clientes_res = supabase.table("clientes").select("id, nombre").execute()
        lista_clientes = clientes_res.data
    except Exception:
        lista_clientes = []
        
    if not lista_clientes:
        st.info("Primero debes registrar clientes en el módulo 'Directorio'.")
        return

    opciones_clientes = {c["nombre"]: c["id"] for c in lista_clientes}
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### Nuevo Embarque")
        with st.form("form_embarque", clear_on_submit=True):
            cliente_sel = st.selectbox("Cliente al que pertenece", options=list(opciones_clientes.keys()))
            bl_number = st.text_input("Número de BL / Booking *")
            origen = st.text_input("Puerto de Origen")
            destino = st.text_input("Puerto de Destino")
            fecha = st.date_input("Fecha del Embarque")
            
            if st.form_submit_button("Registrar Embarque"):
                if bl_number:
                    data = {
                        "cliente_id": opciones_clientes[cliente_sel],
                        "bl_numero": bl_number,
                        "origen": origen,
                        "destino": destino,
                        "fecha": str(fecha)
                    }
                    try:
                        supabase.table("embarques").insert(data).execute()
                        st.success("Embarque registrado exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar. Asegúrate de haber creado la tabla 'embarques'. Detalles: {e}")
                else:
                    st.warning("El número de BL es obligatorio.")
                    
    with col2:
        st.markdown("#### Historial General de Embarques")
        try:
            # Consulta relacional para traer el nombre del cliente
            embarques_res = supabase.table("embarques").select("*, clientes(nombre)").execute()
            
            if embarques_res.data:
                df = pd.DataFrame(embarques_res.data)
                # Extraemos el nombre del cliente del diccionario relacional
                df["Cliente"] = df["clientes"].apply(lambda x: x["nombre"] if isinstance(x, dict) else "Desconocido")
                
                # Ordenamos y renombramos las columnas para la tabla
                df = df[["fecha", "Cliente", "bl_numero", "origen", "destino"]]
                df.columns = ["Fecha", "Cliente", "BL / Booking", "Origen", "Destino"]
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay embarques registrados en el sistema.")
        except Exception as e:
            st.warning("Crea la tabla 'embarques' en Supabase para ver el historial.")
