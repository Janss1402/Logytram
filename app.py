import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import base64
import io
from PIL import Image

# Importaciones para generación de PDF con ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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

if "logo_bytes" not in st.session_state:
    st.session_state.logo_bytes = None

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
# GENERACIÓN DE PDF (REPORTLAB)
# ==========================================
def generar_pdf_reportlab(titulo_reporte, headers, data_rows, kpis=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#1a365d"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#718096"),
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#2c3e50")
    )
    cell_header_style = ParagraphStyle(
        'TableHeaderCell',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        fontName="Helvetica-Bold"
    )

    elements = []

    # Encabezado (Título + Logo)
    header_data = []
    text_header = [
        Paragraph(titulo_reporte, title_style),
        Paragraph("Sistema de Control de Carga y Pagos Logísticos", subtitle_style)
    ]
    
    if st.session_state.logo_bytes:
        try:
            img_io = io.BytesIO(st.session_state.logo_bytes)
            img = Image.open(img_io)
            width, height = img.size
            aspect = height / float(width)
            target_width = 120
            target_height = target_width * aspect
            if target_height > 50:
                target_height = 50
                target_width = target_height / aspect
            
            logo_img = RLImage(io.BytesIO(st.session_state.logo_bytes), width=target_width, height=target_height)
            header_data = [[text_header, logo_img]]
        except Exception:
            header_data = [[text_header, Paragraph("<b>🚢 LOGÍSTICA</b>", subtitle_style)]]
    else:
        header_data = [[text_header, Paragraph("<b>🚢 LOGÍSTICA</b>", subtitle_style)]]

    header_table = Table(header_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor("#2b4c7e")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # KPIs si existen
    if kpis:
        kpi_data = []
        titles = [Paragraph(f"<b>{k['title']}</b>", ParagraphStyle('KPIT', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#4a5568"), alignment=1)) for k in kpis]
        values = [Paragraph(f"<b>{k['value']}</b>", ParagraphStyle('KPIV', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor(k.get('color', "#1a202c")), alignment=1)) for k in kpis]
        
        kpi_table = Table([titles, values], colWidths=[180]*len(kpis))
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f7fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 15))

    # Tabla de Datos
    if headers and data_rows:
        formatted_headers = [Paragraph(h, cell_header_style) for h in headers]
        formatted_rows = []
        for row in data_rows:
            formatted_rows.append([Paragraph(str(cell), cell_style) for cell in row])
        
        table_data = [formatted_headers] + formatted_rows
        col_width = 540 / len(headers)
        data_table = Table(table_data, colWidths=[col_width]*len(headers))
        
        ts = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2b4c7e")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]
        
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                ts.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8fafc")))
                
        data_table.setStyle(TableStyle(ts))
        elements.append(data_table)
    else:
        elements.append(Paragraph("No hay información registrada para mostrar.", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.write(f"👤 **Usuario:** {st.session_state.user.email}")
    if st.button("🚪 Cerrar Sesión"):
        logout()
    
    st.markdown("---")
    st.subheader("🎨 Personalización")
    uploaded_logo = st.file_uploader("Cargar Logo para Reportes (PNG/JPG)", type=["png", "jpg", "jpeg"])
    
    if uploaded_logo is not None:
        st.session_state.logo_bytes = uploaded_logo.read()
        st.success("¡Logo cargado correctamente!")
    
    if st.session_state.logo_bytes:
        st.image(st.session_state.logo_bytes, caption="Logo activo para reportes", use_container_width=True)
        if st.button("❌ Quitar Logo"):
            st.session_state.logo_bytes = None
            st.rerun()

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
    
    kpis_pdf = [
        {"title": "DINERO POR COBRAR", "value": f"${total_cobrar:,.2f}", "color": "#2e7d32"},
        {"title": "CUENTAS POR PAGAR", "value": f"${total_pagar:,.2f}", "color": "#c62828"},
        {"title": "VIAJES ACTIVOS", "value": str(ops_activas), "color": "#1565c0"}
    ]
    
    pdf_dash = generar_pdf_reportlab("Reporte Consolidado - Resumen General", [], [], kpis_pdf)
    st.download_button(
        label="📄 Descargar Reporte General (PDF)",
        data=pdf_dash,
        file_name=f"Reporte_General_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

# ==========================================
# 2. CONTACTOS
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
        st.dataframe(df_contactos, use_container_width=True)

        headers = ["Empresa / Persona", "Contacto", "Teléfono", "Tipo"]
        rows = df_contactos.values.tolist()
        pdf_contactos = generar_pdf_reportlab("Directorio de Clientes y Proveedores", headers, rows)
        
        st.download_button(
            label="📄 Descargar Directorio (PDF)",
            data=pdf_contactos,
            file_name=f"Directorio_Contactos_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# ==========================================
# 3. OPERACIONES
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
        df_ops_view = df_ops[["referencia", "Cliente", "puerto_origen", "puerto_destino", "estado", "fecha_embarque"]]
        st.dataframe(df_ops_view, use_container_width=True)

        headers = ["Referencia", "Cliente", "Origen", "Destino", "Estado", "Fecha"]
        rows = df_ops_view.values.tolist()
        pdf_ops = generar_pdf_reportlab("Reporte de Operaciones y Embarques", headers, rows)
        
        st.download_button(
            label="📄 Descargar Reporte de Operaciones (PDF)",
            data=pdf_ops,
            file_name=f"Reporte_Operaciones_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# ==========================================
# 4. COBROS
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

        headers = ["Operación", "Concepto", "Monto ($)", "Vencimiento"]
        rows = [[c['operaciones']['referencia'], c['concepto'], f"${c['monto']:,.2f}", c['fecha_vencimiento']] for c in cobros_pendientes]
        pdf_cobros = generar_pdf_reportlab("Reporte de Cuentas por Cobrar", headers, rows)
        
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
# 5. PAGOS
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

        headers = ["Proveedor", "Operación", "Concepto", "Monto ($)", "Vencimiento"]
        rows = [
            [
                p['contactos']['nombre_empresa'] if p['contactos'] else 'N/A',
                p['operaciones']['referencia'],
                p['concepto'],
                f"${p['monto']:,.2f}",
                p['fecha_vencimiento']
            ]
            for p in pagos_pendientes
        ]
        pdf_pagos = generar_pdf_reportlab("Reporte de Cuentas por Pagar", headers, rows)
        
        st.markdown("---")
        st.download_button(
            label="📄 Descargar Cuentas por Pagar (PDF)",
            data=pdf_pagos,
            file_name=f"Reporte_Pagos_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("No hay pagos pendientes.")
