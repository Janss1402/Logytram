import os
from datetime import datetime, date
import pandas as pd
import streamlit as st
from fpdf import FPDF


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

  # 2. Cargar Invoices y Pagos de Supabase
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
  except Exception as e:
    st.error(f"Error cargando datos financieros: {e}")
    raw_invoices = []
    raw_pagos = []

  # 3. Procesar balances y mora por factura
  hoy = date.today()
  facturas_procesadas = []
  alertas_30_dias = 0

  for inv in raw_invoices:
    inv_id = inv["id"]
    monto_inicial = float(inv.get("monto", 0.0))
    moneda = inv.get("moneda", "Q")

    pagos_factura = [
        float(p.get("monto", 0.0))
        for p in raw_pagos
        if p.get("invoice_id") == inv_id
    ]
    monto_pagado = sum(pagos_factura)
    saldo_pendiente = max(0.0, monto_inicial - monto_pagado)

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
        "Pagado": monto_pagado,
        "Saldo Pendiente": saldo_pendiente,
        "Días": dias_antiguedad,
        "Estado": estado,
    })

  df_facturas = pd.DataFrame(facturas_procesadas)

  # Pestañas principales
  tab_resumen, tab_invoice, tab_pago, tab_editar = st.tabs([
      "📊 Estado de Cuenta y Alertas",
      "📄 Cargar Nueva Factura",
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
  # TAB 3: REGISTRAR PAGO
  # -------------------------------------------------------------
  with tab_pago:
    st.markdown(f"#### Registrar Pago para: **{cliente_seleccionado}**")
    facturas_pendientes = [
        f for f in facturas_procesadas if f["Saldo Pendiente"] > 0
    ]

    if not facturas_pendientes:
      st.success("🎉 Este cliente no tiene facturas pendientes de pago.")
    else:
      opciones_facturas = {
          (
              f"Factura: {f['No. Factura/Inv']} | Contenedor:"
              f" {f['Contenedor']} | Saldo Pendiente: {f['Moneda']}"
              f" {f['Saldo Pendiente']:,.2f}"
          ): f
          for f in facturas_pendientes
      }

      factura_sel_label = st.selectbox(
          "Seleccione la factura a la que desea aplicar el pago:",
          options=list(opciones_facturas.keys()),
      )
      factura_objeto = opciones_facturas[factura_sel_label]

      st.info(
          f"Aplicando pago a Factura **{factura_objeto['No. Factura/Inv']}**."
          f" Saldo actual: **{factura_objeto['Moneda']}"
          f" {factura_objeto['Saldo Pendiente']:,.2f}**"
      )

      with st.form("form_aplicar_pago_factura", clear_on_submit=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
          referencia = st.text_input(
              "Referencia (No. Transferencia, Cheque, Boleta)"
          )
          fecha_pago = st.date_input("Fecha del Pago", value=hoy)
        with col_p2:
          moneda_pago = st.selectbox(
              "Moneda del Pago",
              [factura_objeto["Moneda"]],
              disabled=True,
          )
          monto_pago = st.number_input(
              "Monto a Abonar/Pagar",
              min_value=0.01,
              max_value=float(factura_objeto["Saldo Pendiente"]),
              value=float(factura_objeto["Saldo Pendiente"]),
              format="%.2f",
          )

        if st.form_submit_button("Aplicar Pago a Factura"):
          try:
            data_pago = {
                "cliente_id": cliente_id,
                "invoice_id": factura_objeto["id"],
                "referencia": referencia,
                "monto": monto_pago,
                "moneda": factura_objeto["Moneda"],
                "fecha": str(fecha_pago),
            }
            supabase.table("pagos").insert(data_pago).execute()
            st.success("Pago aplicado a la factura exitosamente.")
            st.rerun()
          except Exception as e:
            st.error(f"Error al registrar pago: {e}")

  # -------------------------------------------------------------
  # TAB 4: MODIFICAR / ELIMINAR REGISTROS (NUEVO)
  # -------------------------------------------------------------
  with tab_editar:
    st.markdown(
        f"#### Corregir o Eliminar Registros de: **{cliente_seleccionado}**"
    )

    subtab_edit_inv, subtab_edit_pago = st.tabs(
        ["📄 Modificar / Borrar Facturas", "💰 Modificar / Borrar Pagos"]
    )

    # SUBTAB A: EDITAR O BORRAR FACTURAS
    with subtab_edit_inv:
      if not raw_invoices:
        st.info("No hay facturas registradas para modificar.")
      else:
        dict_inv_edit = {
            f"Factura: {inv.get('no_factura','S/N')} | Contenedor:"
            f" {inv.get('contenedor','N/A')} | Fecha: {inv.get('fecha')} |"
            f" Monto: {inv.get('moneda')} {float(inv.get('monto',0)):,.2f}": inv
            for inv in raw_invoices
        }

        inv_label = st.selectbox(
            "Seleccione la factura que desea modificar o eliminar:",
            options=list(dict_inv_edit.keys()),
            key="sel_inv_edit",
        )
        inv_actual = dict_inv_edit[inv_label]

        with st.form("form_editar_factura"):
          st.caption("Modifique los datos erróneos de la factura elegida:")
          col_e1, col_e2 = st.columns(2)
          with col_e1:
            e_no_factura = st.text_input(
                "No. Factura / Invoice", value=inv_actual.get("no_factura", "")
            )
            e_contenedor = st.text_input(
                "Contenedor / Booking", value=inv_actual.get("contenedor", "")
            )
            e_concepto = st.text_input(
                "Concepto", value=inv_actual.get("concepto", "")
            )
          with col_e2:
            e_fecha = st.date_input(
                "Fecha",
                value=datetime.strptime(
                    inv_actual.get("fecha"), "%Y-%m-%d"
                ).date(),
            )
            e_moneda = st.selectbox(
                "Moneda",
                ["USD", "Q"],
                index=0 if inv_actual.get("moneda") == "USD" else 1,
            )
            e_monto = st.number_input(
                "Monto Total",
                value=float(inv_actual.get("monto", 0.0)),
                format="%.2f",
            )

          btn_guardar_e, btn_borrar_e = st.columns(2)
          with btn_guardar_e:
            sub_guardar = st.form_submit_button("💾 Guardar Cambios")
          with btn_borrar_e:
            sub_borrar = st.form_submit_button(
                "🗑️ ELIMINAR FACTURA PERMANENTEMENTE"
            )

          if sub_guardar:
            try:
              up_data = {
                  "no_factura": e_no_factura,
                  "contenedor": e_contenedor,
                  "concepto": e_concepto,
                  "fecha": str(e_fecha),
                  "moneda": e_moneda,
                  "monto": e_monto,
              }
              supabase.table("invoices").update(up_data).eq(
                  "id", inv_actual["id"]
              ).execute()
              st.success("Factura actualizada correctamente.")
              st.rerun()
            except Exception as e:
              st.error(f"Error al actualizar factura: {e}")

          if sub_borrar:
            try:
              supabase.table("invoices").delete().eq(
                  "id", inv_actual["id"]
              ).execute()
              st.success("Factura eliminada del sistema.")
              st.rerun()
            except Exception as e:
              st.error(f"Error al eliminar la factura: {e}")

    # SUBTAB B: EDITAR O BORRAR PAGOS
    with subtab_edit_pago:
      if not raw_pagos:
        st.info("No hay pagos registrados para modificar.")
      else:
        dict_pago_edit = {
            f"Ref: {p.get('referencia','S/N')} | Fecha: {p.get('fecha')} |"
            f" Monto: {p.get('moneda')} {float(p.get('monto',0)):,.2f}": p
            for p in raw_pagos
        }

        pago_label = st.selectbox(
            "Seleccione el pago que desea modificar o eliminar:",
            options=list(dict_pago_edit.keys()),
            key="sel_pago_edit",
        )
        pago_actual = dict_pago_edit[pago_label]

        with st.form("form_editar_pago"):
          st.caption("Modifique los datos erróneos del pago elegido:")
          col_pe1, col_pe2 = st.columns(2)
          with col_pe1:
            pe_referencia = st.text_input(
                "Referencia (No. Cheque / Boleta)",
                value=pago_actual.get("referencia", ""),
            )
            pe_fecha = st.date_input(
                "Fecha del Pago",
                value=datetime.strptime(
                    pago_actual.get("fecha"), "%Y-%m-%d"
                ).date(),
            )
          with col_pe2:
            pe_moneda = st.selectbox(
                "Moneda",
                ["USD", "Q"],
                index=0 if pago_actual.get("moneda") == "USD" else 1,
            )
            pe_monto = st.number_input(
                "Monto Pagado",
                value=float(pago_actual.get("monto", 0.0)),
                format="%.2f",
            )

          btn_guardar_p, btn_borrar_p = st.columns(2)
          with btn_guardar_p:
            sub_guardar_p = st.form_submit_button("💾 Guardar Cambios")
          with btn_borrar_p:
            sub_borrar_p = st.form_submit_button(
                "🗑️ ELIMINAR PAGO PERMANENTEMENTE"
            )

          if sub_guardar_p:
            try:
              up_pago_data = {
                  "referencia": pe_referencia,
                  "fecha": str(pe_fecha),
                  "moneda": pe_moneda,
                  "monto": pe_monto,
              }
              supabase.table("pagos").update(up_pago_data).eq(
                  "id", pago_actual["id"]
              ).execute()
              st.success("Pago actualizado correctamente.")
              st.rerun()
            except Exception as e:
              st.error(f"Error al actualizar pago: {e}")

          if sub_borrar_p:
            try:
              supabase.table("pagos").delete().eq(
                  "id", pago_actual["id"]
              ).execute()
              st.success("Pago eliminado del sistema.")
              st.rerun()
            except Exception as e:
              st.error(f"Error al eliminar pago: {e}")
