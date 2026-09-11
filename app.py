import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import base64
from weasyprint import HTML

# Configuración de página
st.set_page_config(page_title="Control de Logística", page_icon="🚢", layout="wide")

# Conexión a Supabase mediante Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# AUTENTICACIÓN Y SESIÓN
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

# Si no hay usuario en sesión, mostramos únicamente el formulario de login
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
# FUNCION PARA GENERAR REPORTE PDF (WEASYPRINT)
# ==========================================
def generar_pdf_html(titulo_reporte, contenido_html, kpis_html=""):
    """
    Genera un archivo PDF a partir de una plantilla HTML.
    Soporta incrustación de logo en Base64.
    """
    logo_tag = ""
    if st.session_state.logo_base64:
        logo_tag = f'<img src="{st.session_state.logo_base64}" class="logo" />'
    else:
        logo_tag = '<div class="logo-placeholder">🚢 LOGÍSTICA</div>'

    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm 15mm 20mm 15mm;
                @bottom-right {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 8pt;
                    font-family: Arial, sans-serif;
                    color: #666;
                }}
                @bottom-left {{
                    content: "Generado el {fecha_hoy}";
                    font-size: 8pt;
                    font-family: Arial, sans-serif;
                    color: #666;
                }}
            }}
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                color: #2c3e50;
                margin: 0;
                padding: 0;
                font-size: 10pt;
            }}
            .header-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
                border-bottom: 2px solid #2b4c7e;
                padding-bottom: 10px;
            }}
            .header-table td {{
                vertical-align: middle;
            }}
            .title {{
                font-size: 18pt;
                font-weight: bold;
                color: #1a365d;
                margin: 0;
            }}
            .subtitle {{
                font-size: 9pt;
                color: #718096;
                margin-top: 4px;
            }}
            .logo {{
                max-height: 55px;
                max-width: 180px;
                float: right;
            }}
            .logo-placeholder {{
                font-size: 14pt;
                font-weight: bold;
                color: #2b4c7e;
                text-align: right;
            }}
            
            /* KPIs */
            .kpi-container {{
                width: 100%;
                margin-bottom: 20px;
            }}
            .kpi-card {{
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 10px 15px;
                text-align: center;
            }}
            .kpi-title {{
                font-size: 8pt;
                text-transform: uppercase;
                color: #4a5568;
                font-weight: bold;
            }}
            .kpi-value {{
                font-size: 14pt;
                font-weight: bold;
                color: #1a202c;
                margin-top: 5px;
            }}

            /* Tablas */
            table.data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            table.data-table th {{
                background-color: #2b4c7e;
                color: #ffffff;
                text-align: left;
                padding: 8px 10px;
                font-size: 9pt;
                font-weight: bold;
            }}
            table.data-table td {{
                padding: 7px 10px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 9pt;
            }}
            table.data-table tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
            
            .no-data {{
                padding: 20px;
                background-color: #edf2f7;
                text-align: center;
                color: #4a5568;
                border-radius: 4px;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td style="width: 70%;">
                    <div class="title">{titulo_reporte}</div>
                    <div class="subtitle">Sistema de Control de Carga y Pagos Logísticos</div>
                </td>
                <td style="width: 30%; text-align: right;">
                    {logo_tag}
                </td>
            </tr>
        </table>

        {kpis_html}

        {contenido_html}
    </body>
    </html>
    """
    
    return HTML(string=html_template).write_pdf()

# ==========================================
# SIDEBAR (LOGOUT & CONFIGURACIÓN DE LOGO)
# ==========================================
with st.sidebar:
    st.write(f"👤 **Usuario:** {st.session_state.user.email}")
    if st.button("🚪 Cerrar Sesión"):
        logout()
    
    st.markdown("---")
    st.subheader("🎨 Personalización")
    uploaded_logo = st.file_uploader("Cargar Logo para Reportes (PNG/JPG)", type=["png", "jpg", "jpeg"])
    
    if uploaded_logo is not None:
        bytes_data = uploaded_logo.read()
        base64_str = base64.b64encode(bytes_data).decode("utf-8")
        mime_type = uploaded_logo.type
        st.session_state.logo_base64 = f"data:{mime_type};base64,{base64_str}"
        st.success("¡Logo cargado correctamente!")
    
    if st.session_state.logo_base64:
        st.image(st.session_state.logo_base64, caption="Logo activo para reportes", use_container_width=True)
        if st.button("❌ Quitar Logo"):
            st.session_state.logo_base64 = None
            st.rerun()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("🚢 Sistema de Control de Carga y Pagos")

# --- MENÚ PRINCIPAL ---
tab_dash, tab_ops, tab_cobros, tab_pagos, tab_contactos = st.tabs([
    "📊 Resumen Hoy", 
    "🚢 Operaciones (Viajes)", 
    "💰 Por Cobrar", 
    "💸 Por Pagar", 
    "👥 Clientes / Proveedores"
])

# ==========================================
# 1. DASHBOARD / RESUMEN
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
    
    # Generador PDF Resumen General
    kpis_html = f"""
    <table class="kpi-container">
        <tr>
            <td style="width: 33%;">
                <div class="kpi-card">
                    <div class="kpi-title">Dinero Por Cobrar</div>
                    <div class="kpi-value" style="color: #2e7d32;">${total_cobrar:,.2f}</div>
                </div>
            </td>
            <td style="width: 33%;">
                <div class="kpi-card">
                    <div class="kpi-title">Cuentas Por Pagar</div>
                    <div class="kpi-value" style="color: #c62828;">${total_pagar:,.2f}</div>
                </div>
            </td>
            <td style="width: 33%;">
                <div class="kpi-card">
                    <div class="kpi-title">Viajes Activos</div>
                    <div class="kpi-value" style="color: #1565c0;">{ops_activas}</div>
                </div>
            </td>
        </tr>
    </table>
    """
    body_resumen = "<h3>Estado General de la Operación</h3><p>Este informe refleja los balances pendientes de cobro, compromisos de pago activos y el estado de la flota/operaciones en tránsito a la fecha de emisión.</p>"
    
    pdf_dash = generar_pdf_html("Reporte Consolidado - Resumen General", body_resumen, kpis_html)
    st.download_button(
        label="📄 Descargar Reporte General (PDF)",
        data=pdf_dash,
        file_name=f"Reporte_General_{datetime.now().strftime('%Y%m%d')}.pdf",
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

    # Lista de contactos
    data_contactos = supabase.table("contactos").select("*").execute().data
    if data_contactos:
        df_contactos = pd.DataFrame(data_contactos)[["nombre_empresa", "persona_contacto", "telefono", "tipo"]]
        st.dataframe(df_contactos, use_container_width=True)

        # Generador PDF Directorio
        table_html = df_contactos.to_html(classes="data-table", index=False, header=True)
        pdf_contactos = generar_pdf_html("Directorio de Clientes y Proveedores", f"<h3>Lista Registrada</h3>{table_html}")
        
        st.download_button(
            label="📄 Descargar Directorio (PDF)",
            data=pdf_contactos,
            file_name=f"Directorio_Contactos_{datetime.now().strftime('%Y%m%d')}.pdf",
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

    # Ver Operaciones
    ops_data = supabase.table("operaciones").select("*, contactos(nombre_empresa)").execute().data
    if ops_data:
        df_ops = pd.DataFrame(ops_data)
        df_ops['Cliente'] = df_ops['contactos'].apply(lambda x: x['nombre_empresa'] if x else 'N/A')
        df_ops_view = df_ops[["referencia", "Cliente", "puerto_origen", "puerto_destino", "estado", "fecha_embarque"]]
        st.dataframe(df_ops_view, use_container_width=True)

        # Generador PDF Operaciones
        table_html = df_ops_view.to_html(classes="data-table", index=False, header=True)
        pdf_ops = generar_pdf_html("Reporte de Operaciones y Embarques", f"<h3>Historial de Operaciones</h3>{table_html}")
        
        st.download_button(
            label="📄 Descargar Reporte de Operaciones (PDF)",
            data=pdf_ops,
            file_name=f"Reporte_Operaciones_{datetime.now().strftime('%Y%m%d')}.pdf",
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

    # Tabla interactiva
    cobros_pendientes = supabase.table("cobros").select("*, operaciones(referencia)").eq("pagado", False).execute().data
    
    st.subheader("Pendientes por Cobrar")
    if cobros_pendientes:
        for c in cobros_pendientes:
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"**Referencia:** {c['operaciones']['referencia']} | **Monto:** ${c['monto']:,.2f} | **Vence:** {c['fecha_vencimiento']}")
            if col_btn.button("✅ Marcar Pagado", key=f"cobro_{c['id']}"):
                supabase.table("cobros").update({"pagado": True, "fecha_pago": str(datetime.now().date())}).eq("id", c['id']).execute()
                st.rerun()

        # Generador PDF Cobros
        rows_cobros = "".join([
            f"<tr><td>{c['operaciones']['referencia']}</td><td>{c['concepto']}</td><td>${c['monto']:,.2f}</td><td>{c['fecha_vencimiento']}</td></tr>"
            for c in cobros_pendientes
        ])
        html_cobros = f"""
        <h3>Pendientes por Cobrar</h3>
        <table class="data-table">
            <thead>
                <tr><th>Operación</th><th>Concepto</th><th>Monto</th><th>Vencimiento</th></tr>
            </thead>
            <tbody>{rows_cobros}</tbody>
        </table>
        """
        pdf_cobros = generar_pdf_html("Reporte de Cuentas por Cobrar", html_cobros)
        st.markdown("---")
        st.download_button(
            label="📄 Descargar Cuentas por Cobrar (PDF)",
            data=pdf_cobros,
            file_name=f"Reporte_Cobros_{datetime.now().strftime('%Y%m%d')}.pdf",
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

    # Tabla interactiva
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

        # Generador PDF Pagos
        rows_pagos = "".join([
            f"<tr><td>{p['contactos']['nombre_empresa'] if p['contactos'] else 'N/A'}</td><td>{p['operaciones']['referencia']}</td><td>{p['concepto']}</td><td>${p['monto']:,.2f}</td><td>{p['fecha_vencimiento']}</td></tr>"
            for p in pagos_pendientes
        ])
        html_pagos = f"""
        <h3>Pendientes por Pagar a Proveedores</h3>
        <table class="data-table">
            <thead>
                <tr><th>Proveedor</th><th>Operación</th><th>Concepto</th><th>Monto</th><th>Vencimiento</th></tr>
            </thead>
            <tbody>{rows_pagos}</tbody>
        </table>
        """
        pdf_pagos = generar_pdf_html("Reporte de Cuentas por Pagar", html_pagos)
        st.markdown("---")
        st.download_button(
            label="📄 Descargar Cuentas por Pagar (PDF)",
            data=pdf_pagos,
            file_name=f"Reporte_Pagos_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("No hay pagos pendientes.")
