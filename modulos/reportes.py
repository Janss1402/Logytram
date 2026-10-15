from datetime import date, datetime
import os
from fpdf import FPDF
import pandas as pd
import streamlit as st


def limpiar_texto(texto):
    if not texto:
        return ""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def generar_pdf_reporte_mensual(titulo_reporte, df_datos):
    pdf = FPDF()
    pdf.add_page()

    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=30)
        pdf.set_xy(45, 10)
    else:
        pdf.set_xy(10, 10)

    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 10, "LOGYTRAM - REPORTE MENSUAL", ln=1, align="C")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, limpiar_texto(titulo_reporte), ln=1, align="C")
    pdf.cell(
        0,
        8,
        f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ln=1,
        align="C",
    )
    pdf.ln(8)

    # Encabezados de tabla
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(22, 7, "Fecha", border=1)
    pdf.cell(38, 7, "Cliente", border=1)
    pdf.cell(28, 7, "No. Factura", border=1)
    pdf.cell(38, 7, "Contenedor", border=1)
    pdf.cell(16, 7, "Moneda", border=1)
    pdf.cell(25, 7, "Monto", border=1)
    pdf.cell(25, 7, "Saldo", border=1, ln=1)

    # Contenido
    pdf.set_font("helvetica", "", 8)
    if not df_datos.empty:
        for _, row in df_datos.iterrows():
            fec = str(row.get("Fecha", ""))
            cli = limpiar_texto(str(row.get("Cliente", "-")))[:20]
            fact = limpiar_texto(str(row.get("No. Factura/Inv", "-")))[:16]
            cont = limpiar_texto(str(row.get("Contenedor", "-")))[:20]
            mon = str(row.get("Moneda", ""))
            monto = float(row.get("Monto Inicial", 0.0))
            saldo = float(row.get("Saldo Pendiente", 0.0))

            pdf.cell(22, 6, fec, border=1)
            pdf.cell(38, 6, cli, border=1)
            pdf.cell(28, 6, fact, border=1)
            pdf.cell(38, 6, cont, border=1)
            pdf.cell(16, 6, mon, border=1, align="C")
            pdf.cell(25, 6, f"{monto:,.2f}", border=1, align="R")
            pdf.cell(25, 6, f"{saldo:,.2f}", border=1, align="R", ln=1)
    else:
        pdf.cell(0, 8, "No hay registros para este periodo.", border=1, ln=1, align="C")

    return bytes(pdf.output())


def render(supabase):
    st.subheader("📊 Módulo de Reportes Consolidados y Mensuales")
    st.caption("Genera reportes ejecutivos en PDF filtrando por periodo y cliente.")

    hoy = date.today()

    # Cargar Clientes para el filtro opcional
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
        st.error(f"Error cargando directorio de clientes: {e}")

    opciones_clientes = {"-- Todos los Clientes (General) --": None}
    for c in lista_clientes:
        opciones_clientes[c["nombre"]] = c["id"]

    # Controles de Filtrado
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        meses_nombres = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        mes_sel = st.selectbox("Seleccione Mes:", options=list(meses_nombres.keys()), format_func=lambda x: meses_nombres[x], index=hoy.month - 1)
    with col_r2:
        anio_sel = st.number_input("Año:", min_value=2024, max_value=2035, value=hoy.year, step=1)
    with col_r3:
        cliente_label_sel = st.selectbox("Cliente:", options=list(opciones_clientes.keys()))
        cliente_id_sel = opciones_clientes[cliente_label_sel]

    st.markdown("---")

    # Obtención y Procesamiento de Datos
    try:
        if cliente_id_sel:
            # Filtrar por un cliente específico
            inv_res = supabase.table("invoices").select("*, clientes(nombre)").eq("cliente_id", cliente_id_sel).execute()
        else:
            # Consultar todas las facturas globales
            inv_res = supabase.table("invoices").select("*, clientes(nombre)").execute()

        raw_invoices = inv_res.data if inv_res.data else []
        all_pagos = supabase.table("pagos").select("*").execute().data or []
        all_gastos = supabase.table("gastos_invoices").select("*").execute().data or []

        datos_mes = []
        for inv in raw_invoices:
            f_str = inv.get("fecha")
            if not f_str:
                continue
            f_obj = datetime.strptime(f_str, "%Y-%m-%d").date()

            if f_obj.month == mes_sel and f_obj.year == anio_sel:
                inv_id = inv["id"]
                monto_ini = float(inv.get("monto", 0.0))
                mon = inv.get("moneda", "Q")

                p_tot = sum(float(p.get("monto", 0)) for p in all_pagos if p.get("invoice_id") == inv_id)
                g_tot = sum(float(g.get("monto", 0)) for g in all_gastos if g.get("invoice_id") == inv_id)
                saldo_pen = max(0.0, (monto_ini + g_tot) - p_tot)

                nombre_cli = "Desconocido"
                if isinstance(inv.get("clientes"), dict):
                    nombre_cli = inv.get("clientes", {}).get("nombre", "Cliente")
                elif cliente_id_sel:
                    nombre_cli = cliente_label_sel

                datos_mes.append({
                    "Fecha": f_str,
                    "Cliente": nombre_cli,
                    "No. Factura/Inv": inv.get("no_factura") or "S/N",
                    "Contenedor": inv.get("contenedor") or "N/A",
                    "Moneda": mon,
                    "Monto Inicial": monto_ini,
                    "Saldo Pendiente": saldo_pen
                })

        df_reporte = pd.DataFrame(datos_mes)

        st.markdown(f"##### Facturas encontradas para **{meses_nombres[mes_sel]} {anio_sel}**: `{len(df_reporte)}`")

        if not df_reporte.empty:
            st.dataframe(df_reporte, use_container_width=True, hide_index=True)

            titulo_pdf = f"Reporte de {meses_nombres[mes_sel]} {anio_sel}" + (f" - {cliente_label_sel}" if cliente_id_sel else " - Todos los Clientes")
            pdf_bytes = generar_pdf_reporte_mensual(titulo_pdf, df_reporte)

            st.download_button(
                label=f"📄 Descargar Reporte PDF ({meses_nombres[mes_sel]} {anio_sel})",
                data=pdf_bytes,
                file_name=f"Reporte_Mensual_{meses_nombres[mes_sel]}_{anio_sel}.pdf",
                mime="application/pdf",
            )
        else:
            st.info(f"No hay facturas registradas para el periodo {meses_nombres[mes_sel]} {anio_sel}.")

    except Exception as e:
        st.error(f"Error cargando reporte mensual: {e}")
