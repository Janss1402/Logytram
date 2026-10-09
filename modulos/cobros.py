from datetime import date, datetime
import os
from fpdf import FPDF
import pandas as pd
import streamlit as st


def limpiar_texto(texto):
  if not texto:
    return ""
  return str(texto).encode("latin-1", "replace").decode("latin-1")


def generar_pdf_estado_cuenta(
    cliente_nombre, df_resumen_facturas, saldo_q, saldo_usd
):
  pdf = FPDF()
  pdf.add_page()

  logo_path = "assets/logo.png"

  if os.path.exists(logo_path):
    pdf.image(logo_path, x=10, y=8, w=30)
    pdf.set_xy(45, 10)
  else:
    pdf.set_xy(10, 10)

  pdf.set_font("helvetica", "B", 16)
  pdf.cell(0, 10, "LOGYTRAM - ESTADO DE CUENTA", ln=1, align="C")
  pdf.set_font("helvetica", "", 11)
  pdf.cell(0, 8, f"Cliente: {limpiar_texto(cliente_nombre)}", ln=1, align="C")
  pdf.cell(
      0,
      8,
      f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
      ln=1,
      align="C",
  )
  pdf.ln(10)

  pdf.set_font("helvetica", "B", 12)
  pdf.cell(0, 8, "RESUMEN DE SALDOS PENDIENTES", ln=1)
  pdf.set_font("helvetica", "", 11)
  pdf.cell(0, 7, f"Saldo Total Quetzales: Q {saldo_q:,.2f}", ln=1)
  pdf.cell(0, 7, f"Saldo Total Dolares: $ {saldo_usd:,.2f}", ln=1)
  pdf.ln(5)

  pdf.set_font("helvetica", "B", 11)
  pdf.cell(0, 8, "DETALLE DE FACTURAS / INVOICES", ln=1)
  pdf.set_font("helvetica", "", 9)

  if not df_resumen_facturas.empty:
    for _, row in df_resumen_facturas.iterrows():
      fec = row.get("Fecha", "")
      fact = limpiar_texto(row.get("No. Factura/Inv", "-"))
      cont = limpiar_texto(row.get("Contenedor", "-"))
      mon = row.get("Moneda", "")
      monto = row.get("Monto Inicial", 0.0)
      saldo = row.get("Saldo Pendiente", 0.0)
      est = limpiar_texto(row.get("Estado", ""))

      linea = (
          f"Fecha: {fec} | Fact: {fact} | Cont: {cont} | Total: {mon}"
          f" {monto:,.2f} | Saldo: {mon} {saldo:,.2f} | [{est}]"
      )
      pdf.cell(0, 6, linea, ln=1)
  else:
    pdf.cell(0, 7, "No hay registros cargados.", ln=1)

  return bytes(pdf.output())


def render(tipo_cambio, supabase):
  st.subheader("🏢 Gestión de Cobros, Conciliación y Edición")

  # 1. Cargar Clientes
  try:
    clientes_res = (
        supabase.table("clientes")
        .select("id, nombre")
        .order("nombre")
        .execute()
    )
    lista_clientes = clientes_res.data if clientes_res.data else []
  except Exception as e:
    lista_clientes = []
    st.error(f"Error al conectar con clientes: {e}")

  if not lista_clientes:
    st.info("Primero debes registrar clientes en el módulo 'Directorio'.")
    return

  opciones_clientes = {c["nombre"]: c["id"] for c in lista_clientes}
  cliente_seleccionado = st.selectbox(
      "Seleccione un Cliente:", options=list(opciones_clientes.keys())
  )
  cliente_id = opciones_clientes[cliente_seleccionado]

  st.markdown("---")

  # 2. Cargar Invoices, Pagos y Gastos de Supabase
  try:
    inv_res = (
        supabase.table("invoices")
        .select("*")
        .eq("cliente_id", cliente_id)
        .order("fecha", desc=True)
        .execute()
    )
    pagos_res = (
        supabase.table("pagos")
        .select("*")
        .eq("cliente_id", cliente_id)
        .order("fecha", desc=True)
        .execute()
    )

    raw_invoices = inv_res.data if inv_res.data else []
    raw_pagos = pagos_res.data if pagos_res.data else []

    # Cargar gastos de las facturas de este cliente
    invoice_ids = [inv["id"] for inv in raw_invoices]
    raw_gastos = []
    if invoice_ids:
      gastos_res = (
          supabase.table("gastos_invoices")
          .select("*")
          .in_("invoice_id", invoice_ids)
          .order("fecha", desc=True)
          .execute()
      )
      raw_gastos = gastos_res.data if gastos_res.data else []

  except Exception as e:
    st.error(f"Error cargando datos financieros: {e}")
    raw_invoices = []
    raw_pagos = []
    raw_gastos = []

  # 3. Procesar balances, gastos y mora por factura
  hoy = date.today()
  facturas_procesadas = []
  alertas_30_dias = 0

  for inv in raw_invoices:
    inv_id = inv["id"]
    monto_inicial = float(inv.get("monto", 0.0))
    moneda = inv.get("moneda", "Q")

    # Calcular pagos aplicados a esta factura
    pagos_factura = [
        float(p.get("monto", 0.0))
        for p in raw_pagos
        if p.get("invoice_id") == inv_id
    ]
    monto_pagado = sum(pagos_factura)

    # Calcular gastos adicionales de esta factura
    gastos_factura_lista = [
        float(g.get("monto", 0.0))
        for g in raw_gastos
        if g.get("invoice_id") == inv_id
    ]
    total_gastos = sum(gastos_factura_lista)

    # El saldo pendiente toma en cuenta el monto inicial más los gastos adicionales menos los pagos
    saldo_pendiente = max(
        0.0, (monto_inicial + total_gastos) - monto_pagado
    )

    fecha_inv = datetime.strptime(inv["fecha"], "%Y-%m-%d").date()
    dias_antiguedad = (hoy - fecha_inv).days

    if saldo_pendiente <= 0.01:
      estado = "🔵 Pagada"
    elif dias_antiguedad > 30:
      estado = f"🔴 Vencida ({dias_antiguedad} días)"
      alertas_30_dias += 1
    else:
      estado = f"🟢 Al día ({dias_antiguedad} días)"

    facturas_procesadas.append({
        "id": inv_id,
        "Fecha": inv["fecha"],
        "No. Factura/Inv": inv.get("no_factura") or "S/N",
        "Contenedor": inv.get("contenedor") or "N/A",
        "Concepto": inv.get("concepto", ""),
        "Moneda": moneda,
        "Monto Inicial": monto_inicial,
        "Gastos Adicionales": total_gastos,
        "Pagado": monto_pagado,
        "Saldo Pendiente": saldo_pendiente,
        "Días": dias_antiguedad,
        "Estado": estado,
    })

  df_facturas = pd.DataFrame(facturas_procesadas)

  # Pestañas principales
  tab_resumen, tab_invoice, tab_gasto, tab_pago, tab_editar = st.tabs([
      "📊 Estado de Cuenta y Alertas",
      "📄 Cargar Nueva Factura",
      "💸 Gastos Adicionales",
      "💰 Registrar Pago",
      "✏️ Modificar / Eliminar Registros",
  ])

  # -------------------------------------------------------------
  # TAB 1: ESTADO DE CUENTA
  # -------------------------------------------------------------
  with tab_resumen:
    if alertas_30_dias > 0:
      st.error(
          f"🚨 **ALERTA DE MORA:** Este cliente tiene **{alertas_30_dias}**"
          " factura(s) con más de **30 días de antigüedad** y saldo"
          " pendiente."
      )

    if not df_facturas.empty:
      saldo_q = df_facturas[df_facturas["Moneda"] == "Q"][
          "Saldo Pendiente"
      ].sum()
      saldo_usd = df_facturas[df_facturas["Moneda"] == "USD"][
          "Saldo Pendiente"
      ].sum()
    else:
      saldo_q, saldo_usd = 0.0, 0.0

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Saldo Total Pendiente (Quetzales)", f"Q {saldo_q:,.2f}")
    col_m2.metric("Saldo Total Pendiente (Dólares)", f"$ {saldo_usd:,.2f}")

    st.markdown("---")
    st.markdown(
        f"#### Control Individual de Facturas - **{cliente_seleccionado}**"
    )

    if not df_facturas.empty:
      columnas_mostrar = [
          "Fecha",
          "No. Factura/Inv",
          "Contenedor",
          "Concepto",
          "Moneda",
          "Monto Inicial",
          "Gastos Adicionales",
          "Pagado",
          "Saldo Pendiente",
          "Estado",
      ]
      st.dataframe(
          df_facturas[columnas_mostrar],
          use_container_width=True,
          hide_index=True,
      )
    else:
      st.info("No hay facturas cargadas para este cliente.")

    st.markdown("---")
    try:
      pdf_bytes = generar_pdf_estado_cuenta(
          cliente_seleccionado, df_facturas, saldo_q, saldo_usd
      )
      st.download_button(
          label="📄 Descargar Estado de Cuenta Detallado (PDF)",
          data=pdf_bytes,
          file_name=(
              f"Estado_Cuenta_{cliente_seleccionado.replace(' ', '_')}.pdf"
          ),
          mime="application/pdf",
      )
    except Exception as e:
      st.error(f"Error generando PDF: {e}")

  # -------------------------------------------------------------
  # TAB 2: CARGAR NUEVA FACTURA
  # -------------------------------------------------------------
  with tab_invoice:
    st.markdown(
        f"#### Nueva Factura / Cargo para: **{cliente_seleccionado}**"
    )
    with st.form("form_nuevo_inv_det", clear_on_submit=True):
      col_f1, col_f2 = st.columns(2)
      with col_f1:
        no_factura = st.text_input("No. Factura / Invoice *")
        contenedor = st.text_input("No. Contenedor / Booking")
        concepto = st.text_input(
            "Concepto (Ej. Flete, Demoras)", value="Flete y gastos"
        )
      with col_f2:
        fecha_inv = st.date_input("Fecha de Emisión / Cobro", value=hoy)
        moneda_inv = st.selectbox("Moneda", ["USD", "Q"])
        monto_inv = st.number_input(
            "Monto Total de la Factura", min_value=0.01, format="%.2f"
        )

      if st.form_submit_button("Guardar Factura"):
        if no_factura:
          try:
            data_inv = {
                "cliente_id": cliente_id,
                "no_factura": no_factura,
                "contenedor": contenedor,
                "concepto": concepto,
                "monto": monto_inv,
                "moneda": moneda_inv,
                "fecha": str(fecha_inv),
            }
            supabase.table("invoices").insert(data_inv).execute()
            st.success("Factura cargada correctamente.")
            st.rerun()
          except Exception as e:
            st.error(f"Error al guardar factura: {e}")
        else:
          st.warning("El campo 'No. Factura / Invoice' es obligatorio.")

  # -------------------------------------------------------------
  # TAB 3: CARGAR GASTOS ADICIONALES
  # -------------------------------------------------------------
  with tab_gasto:
    st.markdown(
        f"#### 💸 Registrar Gasto Adicional para: **{cliente_seleccionado}**"
    )
    if not raw_invoices:
      st.info(
          "Este cliente no tiene facturas registradas para asociar gastos."
      )
    else:
      opciones_inv_gasto = {
          (
              f"Fact.: {inv.get('no_factura')} | Contenedor:"
              f" {inv.get('contenedor', 'N/A')} | Moneda: {inv.get('moneda')}"
          ): inv["id"]
          for inv in raw_invoices
      }

      sel_inv_gasto_label = st.selectbox(
          "Seleccione la factura de referencia:",
          options=list(opciones_inv_gasto.keys()),
      )
      id_factura_elegida = opciones_inv_gasto[sel_inv_gasto_label]

      with st.form("form_registrar_gasto_adicional", clear_on_submit=True):
        col_g1, col_g2 = st.columns(2)
        with col_g1:
          desc_gasto = st.text_input(
              "Descripción del Gasto (Ej. Timbres, Trámites, Viáticos) *"
          )
          fecha_gasto = st.date_input("Fecha del Gasto", value=hoy)
        with col_g2:
          monto_gasto = st.number_input(
              "Monto del Gasto", min_value=0.01, format="%.2f"
          )

        if st.form_submit_button("Guardar Gasto Adicional"):
          if desc_gasto.strip():
            try:
              data_gasto = {
                  "invoice_id": id_factura_elegida,
                  "descripcion": desc_gasto.strip(),
                  "monto": monto_gasto,
                  "fecha": str(fecha_gasto),
              }
              supabase.table("gastos_invoices").insert(data_gasto).execute()
              st.success("Gasto
