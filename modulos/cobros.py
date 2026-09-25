from datetime import datetime
from fpdf import FPDF
import pandas as pd
import streamlit as st


# Función para limpiar texto y evitar fallos de codificación en fuentes estándar de FPDF
def limpiar_texto(texto):
  if not texto:
    return ""
  return str(texto).encode("latin-1", "replace").decode("latin-1")


def generar_pdf_estado_cuenta(
    cliente_nombre, df_invoices, df_pagos, saldo_q, saldo_usd
):
  pdf = FPDF()
  pdf.add_page()

  # Encabezado
  pdf.set_font("helvetica", "B", 16)
  pdf.cell(0, 10, "ESTADO DE CUENTA", ln=1, align="C")
  pdf.set_font("helvetica", "", 12)
  pdf.cell(0, 10, f"Cliente: {limpiar_texto(cliente_nombre)}", ln=1, align="C")
  pdf.cell(
      0,
      10,
      f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y')}",
      ln=1,
      align="C",
  )
  pdf.ln(5)

  # Resumen de Saldos
  pdf.set_font("helvetica", "B", 12)
  pdf.cell(0, 10, "RESUMEN DE SALDOS PENDIENTES", ln=1)
  pdf.set_font("helvetica", "", 12)
  pdf.cell(0, 8, f"Saldo en Quetzales: Q {saldo_q:,.2f}", ln=1)
  pdf.cell(0, 8, f"Saldo en Dolares: $ {saldo_usd:,.2f}", ln=1)
  pdf.ln(5)

  # Detalle Invoices
  pdf.set_font("helvetica", "B", 12)
  pdf.cell(0, 10, "CARGOS / INVOICES", ln=1)
  pdf.set_font("helvetica", "", 10)
  if not df_invoices.empty:
    for _, row in df_invoices.iterrows():
      conc = limpiar_texto(row.get("concepto", ""))
      mon = row.get("moneda", "")
      monto = row.get("monto", 0)
      fec = row.get("fecha", "")
      pdf.cell(
          0, 8, f"Fecha: {fec} | Concepto: {conc} | Monto: {mon} {monto:,.2f}", ln=1
      )
  else:
    pdf.cell(0, 8, "No hay cargos registrados.", ln=1)

  pdf.ln(5)

  # Detalle Pagos
  pdf.set_font("helvetica", "B", 12)
  pdf.cell(0, 10, "PAGOS RECIBIDOS", ln=1)
  pdf.set_font("helvetica", "", 10)
  if not df_pagos.empty:
    for _, row in df_pagos.iterrows():
      ref = limpiar_texto(row.get("referencia", ""))
      mon = row.get("moneda", "")
      monto = row.get("monto", 0)
      fec = row.get("fecha", "")
      pdf.cell(
          0, 8, f"Fecha: {fec} | Ref: {ref} | Monto: {mon} {monto:,.2f}", ln=1
      )
  else:
    pdf.cell(0, 8, "No hay pagos registrados.", ln=1)

  # Garantiza que retorne bytes para Streamlit
  return bytes(pdf.output())


def render(tipo_cambio, supabase):
  st.subheader("🏢 Gestión de Cobros, Invoices e Historial")

  try:
    clientes_res = (
        supabase.table("clientes").select("id, nombre").order("nombre").execute()
    )
    lista_clientes = clientes_res.data if clientes_res.data else []
  except Exception as e:
    lista_clientes = []
    st.error(f"Error al conectar con la base de clientes: {e}")

  if not lista_clientes:
    st.info("Primero debes registrar clientes en el módulo 'Directorio'.")
    return

  opciones_clientes = {c["nombre"]: c["id"] for c in lista_clientes}
  cliente_seleccionado = st.selectbox(
      "Seleccione un Cliente para operar:", options=list(opciones_clientes.keys())
  )
  cliente_id = opciones_clientes[cliente_seleccionado]

  st.markdown("---")

  tab_resumen, tab_invoice, tab_pago = st.tabs(
      ["📊 Estado de Cuenta", "📄 Nuevo Invoice / Cargo", "💰 Registrar Pago"]
  )

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
        if concepto:
          try:
            data_inv = {
                "cliente_id": cliente_id,
                "concepto": concepto,
                "monto": monto_inv,
                "moneda": moneda_inv,
                "fecha": str(fecha_inv),
            }
            supabase.table("invoices").insert(data_inv).execute()
            st.success("Invoice registrado exitosamente.")
            st.rerun()
          except Exception as e:
            st.error(f"Error al guardar invoice: {e}")
        else:
          st.warning("El concepto es obligatorio.")

  with tab_pago:
    st.markdown(f"#### Registrar pago de: **{cliente_seleccionado}**")
    with st.form("form_nuevo_pago", clear_on_submit=True):
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        referencia = st.text_input("Referencia (No. Cheque, Transferencia)")
        fecha_pago = st.date_input("Fecha del Pago")
      with col_p2:
        moneda_pago = st.selectbox(
            "Moneda del Pago", ["Q", "USD"], key="mon_pago"
        )
        monto_pago = st.number_input(
            "Monto Pagado", min_value=0.01, format="%.2f"
        )

      if st.form_submit_button("Aplicar Pago"):
        try:
          data_pago = {
              "cliente_id": cliente_id,
              "referencia": referencia,
              "monto": monto_pago,
              "moneda": moneda_pago,
              "fecha": str(fecha_pago),
          }
          supabase.table("pagos").insert(data_pago).execute()
          st.success("Pago registrado exitosamente.")
          st.rerun()
        except Exception as e:
          st.error(f"Error al registrar pago: {e}")

  with tab_resumen:
    st.markdown(f"#### Historial de **{cliente_seleccionado}**")

    try:
      invoices_res = (
          supabase.table("invoices")
          .select("*")
          .eq("cliente_id", cliente_id)
          .execute()
      )
      pagos_res = (
          supabase.table("pagos")
          .select("*")
          .eq("cliente_id", cliente_id)
          .execute()
      )

      df_invoices = (
          pd.DataFrame(invoices_res.data)
          if invoices_res.data
          else pd.DataFrame(columns=["fecha", "concepto", "moneda", "monto"])
      )
      df_pagos = (
          pd.DataFrame(pagos_res.data)
          if pagos_res.data
          else pd.DataFrame(columns=["fecha", "referencia", "moneda", "monto"])
      )
    except Exception as e:
      st.error(f"Error al consultar datos: {e}")
      df_invoices = pd.DataFrame(
          columns=["fecha", "concepto", "moneda", "monto"]
      )
      df_pagos = pd.DataFrame(columns=["fecha", "referencia", "moneda", "monto"])

    tot_inv_q = (
        df_invoices[df_invoices["moneda"] == "Q"]["monto"].sum()
        if not df_invoices.empty
        else 0.0
    )
    tot_inv_usd = (
        df_invoices[df_invoices["moneda"] == "USD"]["monto"].sum()
        if not df_invoices.empty
        else 0.0
    )

    tot_pagos_q = (
        df_pagos[df_pagos["moneda"] == "Q"]["monto"].sum()
        if not df_pagos.empty
        else 0.0
    )
    tot_pagos_usd = (
        df_pagos[df_pagos["moneda"] == "USD"]["monto"].sum()
        if not df_pagos.empty
        else 0.0
    )

    saldo_q = tot_inv_q - tot_pagos_q
    saldo_usd = tot_inv_usd - tot_pagos_usd

    m1, m2 = st.columns(2)
    m1.metric("Saldo Pendiente (Quetzales)", f"Q {saldo_q:,.2f}")
    m2.metric("Saldo Pendiente (Dólares)", f"$ {saldo_usd:,.2f}")

    st.markdown("---")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
      st.markdown("**Cargos / Invoices Emitidos**")
      if not df_invoices.empty:
        st.dataframe(
            df_invoices[["fecha", "concepto", "moneda", "monto"]],
            use_container_width=True,
            hide_index=True,
        )
      else:
        st.info("No hay cargos registrados para este cliente.")

    with col_t2:
      st.markdown("**Pagos Recibidos**")
      if not df_pagos.empty:
        st.dataframe(
            df_pagos[["fecha", "referencia", "moneda", "monto"]],
            use_container_width=True,
            hide_index=True,
        )
      else:
        st.info("No hay pagos registrados para este cliente.")

    st.markdown("---")
    try:
      pdf_bytes = generar_pdf_estado_cuenta(
          cliente_seleccionado, df_invoices, df_pagos, saldo_q, saldo_usd
      )
      st.download_button(
          label="📄 Descargar Estado de Cuenta (PDF)",
          data=pdf_bytes,
          file_name=(
              f"Estado_Cuenta_{cliente_seleccionado.replace(' ', '_')}.pdf"
          ),
          mime="application/pdf",
      )
    except Exception as e:
      st.error(f"No se pudo generar el botón de PDF: {e}")
