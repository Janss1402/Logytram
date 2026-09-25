from datetime import date
import sqlite3
import streamlit as st


def obtener_clientes():
  conexion = sqlite3.connect("logytram.db")
  cursor = conexion.cursor()
  cursor.execute("SELECT id, nombre FROM clientes")
  res = cursor.fetchall()
  conexion.close()
  return res


def obtener_invoices_pendientes(cliente_id):
  conexion = sqlite3.connect("logytram.db")
  cursor = conexion.cursor()
  cursor.execute(
      "SELECT id, num_factura, monto_total, moneda, estado FROM invoices WHERE"
      " cliente_id = ? AND estado != 'Pagada'",
      (cliente_id,),
  )
  res = cursor.fetchall()
  conexion.close()
  return res


def render(tipo_cambio):
  st.markdown("## 🏢 Expedientes de Clientes y Control de Invoices / Pagos")
  st.write(
      "Gestión integral por cliente: cartera de facturas pendientes y"
      " acreditación de pagos."
  )

  tab_clientes, tab_invoices, tab_pagos, tab_reporte = st.tabs([
      "👤 1. Expedientes de Clientes",
      "🧾 2. Ingresar Invoices / Facturas",
      "💳 3. Acreditar Pagos a Invoices",
      "📊 4. Estado de Cuenta y Reportes",
  ])

  # --- PESTAÑA 1: CREAR / VER CLIENTES ---
  with tab_clientes:
    st.markdown("### 📂 Registro de Nuevo Expediente de Cliente")
    with st.form("form_nuevo_cliente", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        nombre_cli = st.text_input("Razón Social / Nombre del Cliente").upper()
        nit_cli = st.text_input("NIT / Identificación Tributaria")
        contacto_cli = st.text_input("Persona de Contacto / Encargado")
      with c2:
        tel_cli = st.text_input("Teléfono de Contacto")
        email_cli = st.text_input("Correo Electrónico")
        dir_cli = st.text_area("Dirección Comercial")

      if st.form_submit_button("💾 Crear Expediente de Cliente"):
        if nombre_cli:
          try:
            conexion = sqlite3.connect("logytram.db")
            cursor = conexion.cursor()
            cursor.execute(
                """
                            INSERT INTO clientes (nombre, nit, contacto, telefono, email, direccion)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                (
                    nombre_cli,
                    nit_cli,
                    contacto_cli,
                    tel_cli,
                    email_cli,
                    dir_cli,
                ),
            )
            conexion.commit()
            conexion.close()
            st.success(
                f"✅ Expediente creado con éxito para el cliente:"
                f" {nombre_cli}"
            )
          except Exception as e:
            st.error(
                f"Error (Es posible que el cliente ya exista): {e}"
            )
        else:
          st.warning("⚠️ El nombre del cliente es obligatorio.")

    st.markdown("---")
    st.markdown("### 📋 Clientes Registrados en el Sistema")
    try:
      conexion = sqlite3.connect("logytram.db")
      cursor = conexion.cursor()
      cursor.execute(
          "SELECT id, nombre, nit, telefono, email FROM clientes"
      )
      clientes = cursor.fetchall()
      conexion.close()

      if clientes:
        for cli in clientes:
          st.markdown(
              f"""
                    <div style="background: white; padding: 12px; border-radius: 6px; border-left: 5px solid #004B6E; margin-bottom: 8px;">
                        <b>ID: {cli[0]}</b> | 🏢 <b>{cli[1]}</b> | NIT: {cli[2]} | Tel: {cli[3]} | Email: {cli[4]}
                    </div>
                """,
              unsafe_allow_html=True,
          )
      else:
        st.info("No hay clientes registrados aún.")
    except Exception:
      st.info("Iniciando registros...")

  # --- PESTAÑA 2: INGRESAR INVOICES / FACTURAS ---
  with tab_invoices:
    st.markdown("### 🧾 Generar e Ingresar Invoice / Factura al Expediente")
    lista_cli = obtener_clientes()

    if lista_cli:
      opciones_cli = [f"{item[0]} - {item[1]}" for item in lista_cli]

      with st.form("form_nueva_invoice", clear_on_submit=True):
        sel_cliente = st.selectbox(
            "Seleccionar Cliente (Expediente)", opciones_cli
        )
        cliente_id = int(sel_cliente.split(" - ")[0])

        c1, c2 = st.columns(2)
        with c1:
          num_factura = st.text_input(
              "Número de Factura / Invoice (Ej: INV-2026-001)"
          ).upper()
          hbl_asoc = st.text_input(
              "House B/L (HBL) o Referencia asociada (Opcional)"
          ).upper()
        with c2:
          moneda_inv = st.selectbox(
              "Moneda de Facturación", ["Dólares (USD)", "Quetzales (Q)"]
          )
          monto_total = st.number_input(
              "Monto Total de la Factura", min_value=0.0, value=0.0
          )
          fecha_emision = st.date_input("Fecha de Emisión", value=date.today())

        if st.form_submit_button("💾 Guardar Factura en Expediente"):
          if num_factura and monto_total > 0:
            try:
              conexion = sqlite3.connect("logytram.db")
              cursor = conexion.cursor()
              cursor.execute(
                  """
                                INSERT INTO invoices (cliente_id, num_factura, hbl_asociado, fecha_emision, monto_total, moneda, estado)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                  (
                      cliente_id,
                      num_factura,
                      hbl_asoc,
                      str(fecha_emision),
                      monto_total,
                      moneda_inv,
                      "Pendiente",
                  ),
              )
              conexion.commit()
              conexion.close()
              st.success(
                  f"✅ Factura {num_factura} vinculada al expediente del"
                  " cliente exitosamente."
              )
            except Exception as e:
              st.error(
                  f"Error (Verifique si el número de factura ya existe): {e}"
              )
          else:
            st.warning(
                "Ingrese un número de factura válido y un monto mayor a cero."
            )
    else:
      st.warning(
          "⚠️ Debe registrar al menos un cliente en la pestaña 1 antes de"
          " emitir invoices."
      )

  # --- PESTAÑA 3: ACREDITAR PAGOS ---
  with tab_pagos:
    st.markdown("### 💳 Acreditar Pagos o Abonos a Facturas del Cliente")
    lista_cli = obtener_clientes()

    if lista_cli:
      opciones_cli = [f"{item[0]} - {item[1]}" for item in lista_cli]
      sel_cliente_pago = st.selectbox(
          "Seleccione el Cliente para aplicar pago",
          opciones_cli,
          key="sel_cli_pago",
      )
      cliente_id_pago = int(sel_cliente_pago.split(" - ")[0])

      invoices_pend = obtener_invoices_pendientes(cliente_id_pago)

      if invoices_pend:
        opciones_inv = [
            f"Factura: {inv[1]} | Total: {inv[3]} {inv[2]:,.2f} [Estado: {inv[4]}]"
            for inv in invoices_pend
        ]

        with st.form("form_acreditar_pago", clear_on_submit=True):
          sel_inv = st.selectbox(
              "Seleccione la Factura a Abonar / Pagar", opciones_inv
          )
          # Extraer ID de la factura seleccionada
          # El formato es "Factura: [NUM] | ..." por lo que podemos buscar la coincidencia o indexar
          # Vamos a filtrar el id exacto mapeando de forma limpia:
          idx_seleccionado = opciones_inv.index(sel_inv)
          invoice_id_real = invoices_pend[idx_seleccionado][0]

          c1, c2 = st.columns(2)
          with c1:
            monto_abono = st.number_input(
                "Monto del Abono / Pago Recibido", min_value=0.0, value=0.0
            )
            metodo = st.selectbox(
                "Método de Pago",
                [
                    "Transferencia Bancaria",
                    "Depósito",
                    "Cheque",
                    "Tarjeta de Crédito",
                ],
            )
          with c2:
            referencia = st.text_input(
                "Número de Boleta / Referencia de Banco"
            )
            fecha_pago = st.date_input("Fecha del Abono", value=date.today())

          if st.form_submit_button("✅ Acreditar Pago a Factura"):
            if monto_abono > 0:
              conexion = sqlite3.connect("logytram.db")
              cursor = conexion.cursor()

              # Registrar el pago
              cursor.execute(
                  """
                                INSERT INTO pagos_clientes (invoice_id, fecha_pago, monto_abonado, metodo_pago, referencia_banco)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                  (
                      invoice_id_real,
                      str(fecha_pago),
                      monto_abono,
                      metodo,
                      referencia,
                  ),
              )

              # Calcular si la factura quedó totalmente pagada o parcial
              cursor.execute(
                  "SELECT monto_total FROM invoices WHERE id = ?",
                  (invoice_id_real,),
              )
              monto_total_fac = cursor.fetchone()[0]

              cursor.execute(
                  "SELECT SUM(monto_abonado) FROM pagos_clientes WHERE invoice_id"
                  " = ?",
                  (invoice_id_real,),
              )
              total_abonado = cursor.fetchone()[0] or 0.0

              nuevo_estado = (
                  "Pagada" if total_abonado >= monto_total_fac else "Parcial"
              )

              cursor.execute(
                  "UPDATE invoices SET estado = ? WHERE id = ?",
                  (nuevo_estado, invoice_id_real),
              )

              conexion.commit()
              conexion.close()
              st.success(
                  f"🎉 ¡Pago acreditado con éxito! La factura ahora se encuentra"
                  f" en estado: {nuevo_estado}"
              )
            else:
              st.warning("Ingrese un monto de abono válido.")
      else:
        st.info("✨ Este cliente no tiene facturas pendientes de cobro.")
    else:
      st.info("⚠️ Registre clientes primero.")

  # --- PESTAÑA 4: ESTADO DE CUENTA Y REPORTES ---
  with tab_reporte:
    st.markdown("### 📊 Estado de Cuenta Consolidado por Cliente")
    lista_cli = obtener_clientes()

    if lista_cli:
      opciones_cli = [f"{item[0]} - {item[1]}" for item in lista_cli]
      sel_cli_rep = st.selectbox(
          "Seleccione Cliente para ver Estado de Cuenta",
          opciones_cli,
          key="sel_cli_rep",
      )
      cli_id_rep = int(sel_cli_rep.split(" - ")[0])

      if st.button("🔍 Generar Reporte Financiero del Cliente"):
        conexion = sqlite3.connect("logytram.db")
        cursor = conexion.cursor()

        # Datos del cliente
        cursor.execute(
            "SELECT nombre, nit, telefono, email FROM clientes WHERE id = ?",
            (cli_id_rep,),
        )
        info_c = cursor.fetchone()

        st.markdown(
            f"""
                <div style="background: #E8F0FE; padding: 15px; border-radius: 8px; border-left: 6px solid #004B6E; margin-bottom: 15px;">
                    <h3>Cliente: {info_c[0]}</h3>
                    <p><b>NIT:</b> {info_c[1]} | <b>Teléfono:</b> {info_c[2]} | <b>Email:</b> {info_c[3]}</p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Buscar Invoices del cliente
        cursor.execute(
            """
                SELECT id, num_factura, hbl_asociado, fecha_emision, monto_total, moneda, estado 
                FROM invoices WHERE cliente_id = ?
            """,
            (cli_id_rep,),
        )
        invoices_cliente = cursor.fetchall()

        if invoices_cliente:
          st.markdown("#### 📋 Detalle de Facturas e Invoices Emitidos")
          total_deuda_usd = 0.0
          total_deuda_q = 0.0

          for inv in invoices_cliente:
            inv_id, n_fac, hbl_a, f_em, m_tot, mon, est = inv

            # Calcular pagos abonados a esta factura
            cursor.execute(
                "SELECT SUM(monto_abonado) FROM pagos_clientes WHERE invoice_id"
                " = ?",
                (inv_id,),
            )
            abonado = cursor.fetchone()[0] or 0.0
            saldo_pendiente = m_tot - abonado

            if est != "Pagada":
              if mon == "Dólares (USD)":
                total_deuda_usd += saldo_pendiente
              else:
                total_deuda_q += saldo_pendiente

            color_badge = (
                "#28A745"
                if est == "Pagada"
                else ("#FFA500" if est == "Parcial" else "#FF4B4B")
            )

            st.markdown(
                f"""
                        <div style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #ddd; margin-bottom: 8px;">
                            <b>Factura: {n_fac}</b> | HBL: {hbl_a or 'N/A'} | Fecha: {f_em}<br>
                            <b>Total: {mon} {m_tot:,.2f}</b> | Abonado: {mon} {abonado:,.2f} | <b>Saldo: {mon} {saldo_pendiente:,.2f}</b><br>
                            Estado: <span style="background:{color_badge}; color:white; padding:2px 8px; border-radius:4px; font-weight:bold;">{est}</span>
                        </div>
                    """,
                unsafe_allow_html=True,
            )
        else:
          st.info("Este cliente no cuenta con facturas registradas.")

        conexion.close()
    else:
      st.info("⚠️ No hay clientes registrados para generar reportes.")
