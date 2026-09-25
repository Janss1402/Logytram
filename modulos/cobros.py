import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Función auxiliar para generar PDF
def generar_pdf_estado_cuenta(cliente_nombre, df_invoices, df_pagos, saldo_q, saldo_usd):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "ESTADO DE CUENTA", ln=True, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Cliente: {cliente_nombre}", ln=True, align="C")
    pdf.cell(0, 10, f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(10)
    
    # Resumen de Saldos
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "RESUMEN DE SALDOS PENDIENTES", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Saldo en Quetzales: Q {saldo_q:,.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo en Dólares: $ {saldo_usd:,.2f}", ln=True)
    pdf.ln(10)
    
    # Detalle Invoices
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "CARGOS / INVOICES", ln=True)
    pdf.set_font("helvetica", "", 10)
    for index, row in df_invoices.iterrows():
        pdf.cell(0, 8, f"Fecha: {row['fecha']} | Concepto: {row['concepto']} | Monto: {row['moneda']} {row['monto']}", ln=True)
    pdf.ln(5)
    
    # Detalle Pagos
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "PAGOS RECIBIDOS", ln=True)
    pdf.set_font("helvetica", "", 10)
    for index, row in df_pagos.iterrows():
        pdf.cell(0, 8, f"Fecha: {row['fecha']} | Ref: {row['referencia']} | Monto: {row['moneda']} {row['monto']}", ln=True)
        
    return pdf.output()

def render(tipo_cambio, supabase):
    st.subheader("🏢 Gestión de Cobros, Invoices e Historial")
    
    # 1. Obtener lista de clientes para el selector
    try:
        clientes_res = supabase.table("clientes").select("id, nombre").execute()
        lista_clientes = clientes_res.data
    except Exception:
        lista_clientes = []
        st.warning("No se pudo conectar con la tabla de clientes.")
        
    if not lista_clientes:
        st.info("Primero debes registrar clientes en el módulo 'Directorio'.")
        return

    opciones_clientes = {c["nombre"]: c["id"] for c in lista_clientes}
    cliente_seleccionado = st.selectbox("Seleccione un Cliente para operar:", options=list(opciones_clientes.keys()))
    cliente_id = opciones_clientes[cliente_seleccionado]

    st.markdown("---")

    # 2. Pestañas de operación por cliente
    tab_resumen, tab_invoice, tab_pago = st.tabs(["📊 Estado de Cuenta", "📄 Nuevo Invoice / Cargo", "💰 Registrar Pago"])

    with tab_invoice:
        st.markdown(f"#### Emitir cargo para: **{cliente_seleccionado}**")
        with st.form("form_nuevo_invoice", clear_on_submit=True):
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                concepto = st.text_input("Concepto (Ej. Flete Miami, Demoras, etc.)")
                fecha_inv = st.date_input("Fecha del Cargo")
            with col_i2:
                moneda_inv = st.selectbox("Moneda", ["Q", "USD"], key="mon_inv")
                monto_inv = st.number_input("Monto", min_value=0.01, format="%.2f")
            
            if st.form_submit_button("Guardar Invoice"):
                data_inv = {
                    "cliente_id": cliente_id,
                    "concepto": concepto,
                    "monto": monto_inv,
                    "moneda": moneda_inv,
                    "fecha": str(fecha_inv)
                }
                supabase.table("invoices").insert(data_inv).execute()
                st.success("Invoice registrado exitosamente.")
                st.rerun()

    with tab_pago:
        st.markdown(f"#### Registrar pago de: **{cliente_seleccionado}**")
        with st.form("form_nuevo_pago", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                referencia = st.text_input("Referencia (No. Cheque, Transferencia)")
                fecha_pago = st.date_input("Fecha del Pago")
            with col_p2:
                moneda_pago = st.selectbox("Moneda del Pago", ["Q", "USD"], key="mon_pago")
                monto_pago = st.number_input("Monto Pagado", min_value=0.01, format="%.2f")
            
            if st.form_submit_button("Aplicar Pago"):
                data_pago = {
                    "cliente_id": cliente_id,
                    "referencia": referencia,
                    "monto": monto_pago,
                    "moneda": moneda_pago,
                    "fecha": str(fecha_pago)
                }
                supabase.table("pagos").insert(data_pago).execute()
                st.success("Pago registrado exitosamente.")
                st.rerun()

    with tab_resumen:
        st.markdown(f"#### Historial de **{cliente_seleccionado}**")
        
        # Extraer datos de Supabase
        invoices_res = supabase.table("invoices").select("*").eq("cliente_id", cliente_id).execute()
        pagos_res = supabase.table("pagos").select("*").eq("cliente_id", cliente_id).execute()
        
        df_invoices = pd.DataFrame(invoices_res.data) if invoices_res.data else pd.DataFrame(columns=["fecha", "concepto", "moneda", "monto"])
        df_pagos = pd.DataFrame(pagos_res.data) if pagos_res.data else pd.DataFrame(columns=["fecha", "referencia", "moneda", "monto"])
        
        # Cálculos de saldos separados por moneda
        tot_inv_q = df_invoices[df_invoices['moneda'] == 'Q']['monto'].sum() if not df_invoices.empty else 0
        tot_inv_usd = df_invoices[df_invoices['moneda'] == 'USD']['monto'].sum() if not df_invoices.empty else 0
        
        tot_pagos_q = df_pagos[df_pagos['moneda'] == 'Q']['monto'].sum() if not df_pagos.empty else 0
        tot_pagos_usd = df_pagos[df_pagos['moneda'] == 'USD']['monto'].sum() if not df_pagos.empty else 0
        
        saldo_q = tot_inv_q - tot_pagos_q
        saldo_usd = tot_inv_usd - tot_pagos_usd

        # Métricas visuales
        m1, m2 = st.columns(2)
        m1.metric("Saldo Pendiente (Quetzales)", f"Q {saldo_q:,.2f}")
        m2.metric("Saldo Pendiente (Dólares)", f"$ {saldo_usd:,.2f}")
        
        st.markdown("---")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("**Cargos / Invoices Emitidos**")
            st.dataframe(df_invoices[["fecha", "concepto", "moneda", "monto"]], use_container_width=True, hide_index=True)
        with col_t2:
            st.markdown("**Pagos Recibidos**")
            st.dataframe(df_pagos[["fecha", "referencia", "moneda", "monto"]], use_container_width=True, hide_index=True)

        # Generación de PDF
        st.markdown("---")
        pdf_bytes = generar_pdf_estado_cuenta(cliente_seleccionado, df_invoices, df_pagos, saldo_q, saldo_usd)
        
        st.download_button(
            label="📄 Descargar Estado de Cuenta (PDF)",
            data=pdf_bytes,
            file_name=f"Estado_Cuenta_{cliente_seleccionado}.pdf",
            mime="application/pdf"
        )
