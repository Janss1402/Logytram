import streamlit as st

def render(tipo_cambio, supabase):
    st.subheader("💸 Gestión de Pagos a Proveedores")
    st.info(f"Tipo de cambio actual: Q. {tipo_cambio}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### Registrar Egreso")
        with st.form("form_pagos_proveedores", clear_on_submit=True):
            proveedor = st.text_input("Nombre del Proveedor (Ej. Naviera, Transporte)")
            concepto = st.text_input("Concepto (Ej. Pago de Flete, Almacenaje)")
            monto = st.number_input("Monto a Pagar", min_value=0.01)
            moneda = st.selectbox("Moneda", ["Q", "USD"])
            
            if st.form_submit_button("Registrar Pago"):
                # Aquí puedes agregar luego la tabla "egresos" en Supabase
                st.success(f"Pago a {proveedor} registrado exitosamente (Función en desarrollo).")
                
    with col2:
        st.markdown("#### Historial de Egresos")
        st.write("Aquí aparecerá la tabla con los pagos realizados a proveedores y los comprobantes correspondientes.")
