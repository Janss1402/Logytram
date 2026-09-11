import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

st.set_page_config(page_title="Pagos", page_icon="💸", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor inicia sesión en la página principal.")
    st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("💸 Cuentas Por Pagar (Costos y Navieras)")

ops_res = supabase.table("operaciones").select("id, referencia").execute().data
dict_ops = {o['referencia']: o['id'] for o in ops_res} if ops_res else {}

provs_res = supabase.table("contactos").select("id, nombre_empresa").neq("tipo", "Cliente").execute().data
dict_provs = {p['nombre_empresa']: p['id'] for p in provs_res} if provs_res else {}

with st.expander("➕ REGISTRAR NUEVO PAGO PENDIENTE", expanded=False):
    if not dict_ops or not dict_provs:
        st.warning("⚠️ Necesitas registrar al menos una Operación y un Proveedor.")
    else:
        with st.form("form_pago"):
            op_sel = st.selectbox("Asociado al Embarque*", list(dict_ops.keys()))
            prov_sel = st.selectbox("Pagar a (Naviera/Proveedor)*", list(dict_provs.keys()))
            monto = st.number_input("Monto a Pagar ($)*", min_value=0.0, step=50.0)
            concepto = st.text_input("Concepto de Gasto", value="Flete Naviera")
            vencimiento = st.date_input("Fecha Vencimiento Factura", date.today())
            
            if st.form_submit_button("Registrar Pago Pendiente", use_container_width=True):
                if monto > 0:
                    supabase.table("pagos").insert({
                        "operacion_id": dict_ops[op_sel],
                        "proveedor_id": dict_provs[prov_sel],
                        "monto": monto,
                        "concepto": concepto,
                        "fecha_vencimiento": str(vencimiento)
                    }).execute()
                    st.success("✅ Pago registrado.")
                    st.rerun()
                else:
                    st.error("El monto debe ser mayor a 0.")

st.subheader("⚠️ Facturas/Gastos Pendientes por Pagar")
pagos_pendientes = supabase.table("pagos").select("*, operaciones(referencia), contactos(nombre_empresa)").eq("pagado", False).order("fecha_vencimiento").execute().data

if pagos_pendientes:
    for p in pagos_pendientes:
        ref_bl = p['operaciones']['referencia'] if p['operaciones'] else "N/A"
        prov_nombre = p['contactos']['nombre_empresa'] if p['contactos'] else "N/A"
        with st.container():
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"🏢 **A:** {prov_nombre} | **Monto:** ${p['monto']:,.2f} | **Vence:** {p['fecha_vencimiento']} | *(Ref: {ref_bl})*")
            if col_btn.button("✅ Marcar Pagado", key=f"pago_{p['id']}", use_container_width=True):
                supabase.table("pagos").update({"pagado": True, "fecha_pago": str(date.today())}).eq("id", p['id']).execute()
                st.success("¡Pago registrado!")
                st.rerun()
            st.divider()
else:
    st.success("🎉 ¡No hay pagos pendientes con proveedores!")
