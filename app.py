import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import base64
from weasyprint import HTML

# Configuración de página
st.set_page_config(page_title="Control de Logística", page_icon="🚢", layout="wide")

# ==========================================
# CONEXIÓN A SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# AUTENTICACIÓN
# ==========================================
if "user" not in st.session_state:
    st.session_state.user = None

if "logo_base64" not in st.session_state:
    st.session_state.logo_base64 = None

def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = response.user
        st.success("¡Inicio de sesión exitoso!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al iniciar sesión: {e}")

def logout():
    try:
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    except Exception as e:
        st.error(f"Error al cerrar sesión: {e}")

# Pantalla de Login si no hay sesión
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🚢 Control de Logística")
        st.subheader("Iniciar Sesión")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar")
            if submit:
                if email and password:
                    login(email, password)
                else:
                    st.warning("Por favor completa ambos campos.")
    st.stop()

# ==========================================
# FUNCION GENERADORA DE PDF (WEASYPRINT)
# ==========================================
def generar_pdf_reporte(titulo_reporte: str, df: pd.DataFrame, resumen_kpi: dict = None) -> bytes:
    """Genera un archivo PDF estilizado con encabezado, logo y datos."""
    
    # Preparar logo en HTML si existe
    logo_html = ""
    if st.session_state.logo_base64:
        logo_html = f'<img src="data:image/png;base64,{st.session_state.logo_base64}" class="logo"/>'
    else:
        logo_html = '<div class="logo-placeholder">🚢 LOGO EMPRESA</div>'

    # Sección opcional de KPIs (para Dashboard/Resumen)
    kpi_html = ""
    if resumen_kpi:
        kpi_html = '<div class="kpi-container">'
        for k, v in resumen_kpi.items():
            kpi_html += f'<div class="kpi-card"><div class="kpi-title">{k}</div><div class="kpi-value">{v}</div></div>'
        kpi_html += '</div>'

    # Convertir DataFrame a Tabla HTML limpia
    tabla_html = df.to_html(index=False, classes="data-table", escape=False) if not df.empty else "<p>No hay datos registrados.</p>"

    fecha_emision = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4 portrait;
                margin: 15mm 12mm;
                @bottom-right {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-family: Arial, sans-serif;
                    font-size: 8pt;
                    color: #666;
                }}
            }}
            body {{
                font-family: Arial, sans-serif;
                color: #222;
                margin: 0;
                padding: 0;
                font-size: 10pt;
            }}
            .header-table {{
                width: 100%;
                border-collapse: collapse;
                border-bottom: 2px solid #1a365d;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .header-table td {{
                vertical-align: middle;
            }}
            .logo {{
                max-height: 55px;
                max-width: 180px;
                object-fit: contain;
            }}
            .logo-placeholder {{
                font-weight: bold;
                font-size: 14pt;
                color: #1a365d;
            }}
            .title-section {{
                text-align: right;
            }}
            .report-title {{
                font-size: 16pt;
                font-weight: bold;
                color: #1a365d;
                margin: 0;
            }}
            .report-date {{
                font-size: 8pt;
                color: #666;
                margin-top: 4px;
            }}
            
            /* KPIs */
            .kpi-container {{
                display: table;
                width: 100%;
                margin-bottom: 20px;
            }}
            .kpi-card {{
                display: table-cell;
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 10px;
                text-align: center;
                width: 30%;
            }}
            .kpi-title {{
                font-size: 8pt;
                color: #4a5568;
                text-transform: uppercase;
                font-weight: bold;
            }}
            .kpi-value {{
                font-size: 13pt;
                font-weight: bold;
                color: #2b6cb0;
                margin-top: 4px;
            }}

            /* TABLA */
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            .data-table th {{
                background-color: #2b6cb0;
                color: #ffffff;
                text-align: left;
                padding: 8px;
                font-size: 9pt;
                font-weight: bold;
            }}
            .data-table td {{
                padding: 7px 8px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 8.5pt;
            }}
            .data-table tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td>{logo_html}</td>
                <td class="title-section">
                    <div class="report-title">{titulo_reporte}</div>
                    <div class="report-date">Emitido: {fecha_emision}</div>
                </td>
            </tr>
        </table>

        {kpi_html}

        <h3 style="color: #1a365d; margin-bottom: 8px;">Detalle de Registros</h3>
        {tabla_html}
    </body>
    </html>
    """

    return HTML(string=html_content).write_pdf()

# ==========================================
# BARRA LATERAL (CONFIGURACIÓN Y LOGOUT)
# ==========================================
with st.sidebar:
    st.write(f"👤 **Usuario:** {st.session_state.user.email}")
    if st.button("🚪 Cerrar Sesión"):
        logout()

    st.markdown("---")
    st.subheader("🖼️ Configuración del Logo")
    uploaded_logo = st.file_uploader("Cargar Logo para Reportes PDF", type=["png", "jpg", "jpeg"])
    
    if uploaded_logo is not None:
        bytes_data = uploaded_logo.read()
        st.session_state.logo_base64 = base64.b64encode(bytes_data).decode()
        st.success("¡Logo cargado correctamente!")
        st.image(uploaded_logo, width=150)
    elif st.session_state.logo_base64:
        st.info("Logo configurado actualmente:")
        st.image(base64.b64decode(st.session_state.logo_base64), width=150)

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("🚢 Sistema de Control de Carga y Pagos")

tab_dash, tab_ops, tab_cobros, tab_pagos, tab_contactos = st.tabs([
    "📊 Resumen Hoy", 
    "🚢 Operaciones (Viajes)", 
    "💰 Por Cobrar", 
    "💸 Por Pagar", 
    "👥 Clientes / Proveedores"
])

# ==========================================
# 1. DASHBOARD
# ==========================================
with tab_dash:
    st.header("Estado General de la Empresa")
    
    res_cobros = supabase.table("cobros").select("monto").eq("pagado", False).execute()
    res_pagos = supabase.table("pagos").select("monto").eq("pagado", False).execute()
    res_ops = supabase.table("operaciones").select("id").eq("estado", "En Tránsito").execute()
    
    total_cobrar = sum([item['monto'] for item in res_cobros.data]) if res_cobros.data else 0.0
    total_pagar = sum([item['monto'] for item in res_pagos.data]) if res_pagos.data else 0.0
    ops_activas = len(res_ops.data) if res_ops.data else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Dinero Por Cobrar", f"${total_cobrar:,.2f}")
    col2.metric("🔴 Cuentas Por Pagar", f"${total_pagar:,.2f}")
    col3.metric("🚢 Embargos/Viajes Activos", ops_activas)

    st.markdown("---")
    
    # PDF de Resumen
    ops_todas = supabase.table("operaciones").select("referencia, puerto_origen, puerto_destino, estado, fecha_embarque").execute().data
    df_resumen = pd.DataFrame(ops_todas) if ops_todas else pd.DataFrame()
    
    kpis = {
        "Por Cobrar": f"${total_cobrar:,.2f}",
        "Por Pagar": f"${total_pagar:,.2f}",
        "Viajes Activos": str(ops_activas)
    }
    
    if not df_resumen.empty:
        pdf_resumen = generar_pdf_reporte("Reporte General de Operaciones y Estado", df_resumen, resumen_kpi=kpis)
        st.download_button(
            label="📄 Descargar Reporte General (PDF)",
            data=pdf_resumen,
            file_name=f"reporte_general_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# ==========================================
# 2. REGISTRO DE CONTACTOS / DIRECTORIO
# ==========================================
with tab_contactos:
    st.header("Clientes y Proveedores")
    
    with st.expander("➕ Registrar Nuevo Cliente o Naviera", expanded=False):
        with st.form("form_contacto"):
            nombre = st.text_input("Nombre de la Empresa o Persona*")
            contacto = st.text_input("Atención con / Persona de contacto")
            tel = st.text_input("Teléfono / WhatsApp")
            tipo = st.selectbox("Tipo", ["Cliente", "Naviera", "Transportista", "Otro"])
            
            if st.form_submit_button("Guardar Contacto"):
                if nombre:
                    supabase.table("contactos").insert({
                        "nombre_empresa": nombre,
                        "persona_contacto": contacto,
                        "telefono": tel,
                        "tipo": tipo
                    }).execute()
                    st.success("Guardado con éxito!")
                    st.rerun()
                else:
                    st.error("Ingresa al menos el nombre.")

    data_contactos = supabase.table("contactos").select("*").execute().data
    if data_contactos:
        df_contactos = pd.DataFrame(data_contactos)[["nombre_empresa", "persona_contacto", "telefono", "tipo"]]
        df_contactos.columns = ["Empresa", "Contacto", "Teléfono", "Tipo"]
        st.dataframe(df_contactos, use_container_width=True)

        pdf_contactos = generar_pdf_reporte("Directorio de Clientes y Proveedores", df_contactos)
        st.download_button(
            label="📄 Descargar Directorio (PDF)",
            data=pdf_contactos,
            file_name=f"directorio_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# ==========================================
# 3. OPERACIONES / EMBARQUES
# ==========================================
with tab_ops:
    st.header("Viajes y Embarques")
    
    contactos = supabase.table("contactos").select("id, nombre_empresa").eq("tipo", "Cliente").execute().data
    dict_clientes = {c['nombre_empresa']: c['id'] for c in contactos} if contactos else {}

    with st.expander("➕ Abrir Nueva Operación / Embarque", expanded=False):
        if not dict_clientes:
            st.warning("Primero registra al menos un cliente en la pestaña 'Clientes / Proveedores'.")
        else:
            with st.form("form_op"):
                ref = st.text_input("Referencia / No. de Contenedor / Buque*", placeholder="Ej: BL-98012 / MSC Isabel")
                cliente_sel = st.selectbox("Cliente*", list(dict_clientes.keys()))
                origen = st.text_input("Puerto de Origen", placeholder="Ej: Ningbo, China")
                destino = st.text_input("Puerto de Destino", placeholder="Ej: Manzanillo, México")
                fecha = st.date_input("Fecha de Embarque", datetime.now())
                
                if st.form_submit_button("Crear Operación"):
                    supabase.table("operaciones").insert({
                        "referencia": ref,
                        "cliente_id": dict_clientes[cliente_sel],
                        "puerto_origen": origen,
                        "puerto_destino": destino,
                        "fecha_embarque": str(fecha)
                    }).execute()
                    st.success("Operación registrada correctamente!")
                    st.rerun()

    ops_data = supabase.table("operaciones").select("*, contactos(nombre_empresa)").execute().data
    if ops_data:
        df_ops = pd.DataFrame(ops_data)
        df_ops['Cliente'] = df_ops['contactos'].apply(lambda x: x['nombre_empresa'] if x else 'N/A')
        df_ops_mostrar = df_ops[["referencia", "Cliente", "puerto_origen", "puerto_destino", "estado", "fecha_embarque"]]
        df_ops_mostrar.columns = ["Referencia / BL", "Cliente", "Origen", "Destino", "Estado", "Fecha Embarque"]
        
        st.dataframe(df_ops_mostrar, use_container_width=True)

        pdf_ops = generar_pdf_reporte("Reporte de Operaciones y Embarques", df_ops_mostrar)
        st.download_button(
            label="📄 Descargar Reporte de Operaciones (PDF)",
            data=pdf_ops,
            file_name=f"reporte_operaciones_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# ==========================================
# 4. CUENTAS POR COBRAR
# ==========================================
with tab_cobros:
    st.header("Cobros a Clientes")
    
    ops = supabase.table("operaciones").select("id, referencia").execute().data
    dict_ops = {o['referencia']: o['id'] for o in ops} if ops else {}

    with st.expander("➕ Registrar Cobro / Factura Emitida", expanded=False):
        if not dict_ops:
            st.warning("Primero registra una Operación.")
        else:
            with st.form("form_cobro"):
                op_sel = st.selectbox("Operación / BL*", list(dict_ops.keys()))
                monto = st.number_input("Monto a Cobrar ($)*", min_value=0.0, step=100.0)
                concepto = st.text_input("Concepto", value="Flete Marítimo y Gastos de Puerto")
                vencimiento = st.date_input("Fecha Límite de Pago")
                
                if st.form_submit_button("Guardar Cobro"):
                    supabase.table("cobros").insert({
                        "operacion_id": dict_ops[op_sel],
                        "monto": monto,
                        "concepto": concepto,
                        "fecha_vencimiento": str(vencimiento)
                    }).execute()
                    st.success("Cobro agendado!")
                    st.rerun()

    cobros_pendientes = supabase.table("cobros").select("*, operaciones(referencia)").eq("pagado", False).execute().data
    
    st.subheader("Pendientes por Cobrar")
    if cobros_pendientes:
        for c in cobros_pendientes:
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"**Referencia:** {c['operaciones']['referencia']} | **Monto:** ${c['monto']:,.2f} | **Vence:** {c['fecha_vencimiento']}")
            if col_btn.button("✅ Marcar Pagado", key=f"cobro_{c['id']}"):
                supabase.table("cobros").update({"pagado": True, "fecha_pago": str(datetime.now().date())}).eq("id", c['id']).execute()
                st.rerun()

        # Preparar reporte PDF
        list_cobros = []
        for c in cobros_pendientes:
            list_cobros.append({
                "Operación": c['operaciones']['referencia'] if c['operaciones'] else "N/A",
                "Concepto": c['concepto'],
                "Monto ($)": f"${c['monto']:,.2f}",
                "Vencimiento": c['fecha_vencimiento']
            })
        df_cobros_pdf = pd.DataFrame(list_cobros)
        pdf_cobros = generar_pdf_reporte("Reporte de Cuentas por Cobrar", df_cobros_pdf)
        
        st.markdown("---")
        st.download_button(
            label="📄 Descargar Reporte Por Cobrar (PDF)",
            data=pdf_cobros,
            file_name=f"reporte_por_cobrar_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("¡Excelente! No hay cobros pendientes.")

# ==========================================
# 5. CUENTAS POR PAGAR
# ==========================================
with tab_pagos:
    st.header("Pagos a Navieras y Proveedores")
    
    provs = supabase.table("contactos").select("id, nombre_empresa").neq("tipo", "Cliente").execute().data
    dict_provs = {p['nombre_empresa']: p['id'] for p in provs} if provs else {}

    with st.expander("➕ Registrar Factura / Cuenta por Pagar", expanded=False):
        if not dict_ops or not dict_provs:
            st.warning("Necesitas tener al menos una operación y un proveedor registrado.")
        else:
            with st.form("form_pago"):
                op_sel = st.selectbox("Asociado a la Operación*", list(dict_ops.keys()))
                prov_sel = st.selectbox("Proveedor / Naviera*", list(dict_provs.keys()))
                monto = st.number_input("Monto a Pagar ($)*", min_value=0.0, step=100.0)
                concepto = st.text_input("Concepto", value="Flete Naviera")
                vencimiento = st.date_input("Fecha Vencimiento Factura")
                
                if st.form_submit_button("Guardar Pago"):
                    supabase.table("pagos").insert({
                        "operacion_id": dict_ops[op_sel],
                        "proveedor_id": dict_provs[prov_sel],
                        "monto": monto,
                        "concepto": concepto,
                        "fecha_vencimiento": str(vencimiento)
                    }).execute()
                    st.success("Pago registrado!")
                    st.rerun()

    pagos_pendientes = supabase.table("pagos").select("*, operaciones(referencia), contactos(nombre_empresa)").eq("pagado", False).execute().data
    
    st.subheader("Pendientes por Pagar")
    if pagos_pendientes:
        for p in pagos_pendientes:
            col_info, col_btn = st.columns([3, 1])
            prov_nombre = p['contactos']['nombre_empresa'] if p['contactos'] else "N/A"
            col_info.write(f"**A:** {prov_nombre} | **Monto:** ${p['monto']:,.2f} | **Vence:** {p['fecha_vencimiento']} (Op: {p['operaciones']['referencia']})")
            if col_btn.button("✅ Marcar Pagado", key=f"pago_{p['id']}"):
                supabase.table("pagos").update({"pagado": True, "fecha_pago": str(datetime.now().date())}).eq("id", p['id']).execute()
                st.rerun()

        # Preparar reporte PDF
        list_pagos = []
        for p in pagos_pendientes:
            list_pagos.append({
                "Proveedor / Naviera": p['contactos']['nombre_empresa'] if p['contactos'] else "N/A",
                "Operación": p['operaciones']['referencia'] if p['operaciones'] else "N/A",
                "Concepto": p['concepto'],
                "Monto ($)": f"${p['monto']:,.2f}",
                "Vencimiento": p['fecha_vencimiento']
            })
        df_pagos_pdf = pd.DataFrame(list_pagos)
        pdf_pagos = generar_pdf_reporte("Reporte de Cuentas por Pagar", df_pagos_pdf)
        
        st.markdown("---")
        st.download_button(
            label="📄 Descargar Reporte Por Pagar (PDF)",
            data=pdf_pagos,
            file_name=f"reporte_por_pagar_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("No hay pagos pendientes.")
