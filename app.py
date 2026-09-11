import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Control de Logística", page_icon="🚢", layout="wide")

# Conexión a Supabase mediante Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

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
# 1. DASHBOARD
# ==========================================
with tab_dash:
    st.header("Estado General de la Empresa")
    
    # Consultas rápidas
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
    st.subheader("⚠️ Recordatorios Importantes")
    st.info("💡 Consejo para el usuario: Revisa la sección 'Por Cobrar' diariamente para gestionar seguimientos.")

# ==========================================
# 2. REGISTRO DE CONTACTOS
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
        st.dataframe(pd.DataFrame(data_contactos)[["nombre_empresa", "persona_contacto", "telefono", "tipo"]], use_container_width=True)

# ==========================================
# 3. OPERACIONES / EMBARQUES
# ==========================================
with tab_ops:
    st.header("Viajes y Embarques")
    
    # Cargar contactos para el selector
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
        st.dataframe(df_ops[["referencia", "Cliente", "puerto_origen", "puerto_destino", "estado", "fecha_embarque"]], use_container_width=True)

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

    # Tabla interactiva para marcar como Pagado
    cobros_pendientes = supabase.table("cobros").select("*, operaciones(referencia)").eq("pagado", False).execute().data
    
    st.subheader("Pendientes por Cobrar")
    if cobros_pendientes:
        for c in cobros_pendientes:
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"**Referencia:** {c['operaciones']['referencia']} | **Monto:** ${c['monto']:,.2f} | **Vence:** {c['fecha_vencimiento']}")
            if col_btn.button("✅ Marcar Pagado", key=f"cobro_{c['id']}"):
                supabase.table("cobros").update({"pagado": True, "fecha_pago": str(datetime.now().date())}).eq("id", c['id']).execute()
                st.rerun()
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

    # Tabla interactiva para marcar como Pagado
    pagos_pendientes = supabase.table("pagos").select("*, operaciones(referencia), contactos(nombre_empresa)").eq("pagado", False).execute().data
    
    st.subheader("Pendientes por Pagar")
    if pagos_pendientes:
        for p in pagos_pendientes:
            col_info, col_btn = st.columns([3, 1])
            prov_nombre = p['contactos']['nombre_empresa'] if p['contactos'] else "N/A"
            col_info.write(f"**A:** {prov_nombre} | **Monto:** ${p['monto']:,.2f} | **Vence:** {p['fecha_vencimiento']} (Op: {p['operaciones']['referencia']})")
            if col_btn.button("✅ Marcar Pagado", key=f"pago_{p['id']}"):
                supabase.table("pagos").update({"pagado": True, "fecha_pago": str(datetime.now().date())}).eq("id", c['id']).execute()
                st.rerun()
    else:
        st.info("No hay pagos pendientes pendientes.")
