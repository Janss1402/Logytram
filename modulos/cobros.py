import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

st.set_page_config(page_title="Cobros", page_icon="💰", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor inicia sesión en la página principal.")
    st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("💰 Cuentas Por Cobrar (Facturación)")

ops_res = supabase.table("operaciones").select("id, referencia").execute().data
dict_ops = {o['referencia']: o['id'] for o in ops_res} if ops_res else {}

with st.expander("➕ REGISTRAR NUEVO COBRO", expanded=False):
    if not dict_ops:
        st.warning("⚠️ Debes tener al menos un Embarque registrado.")
    else:
        with st.form("form_cobro"):
            op_sel = st.selectbox("Seleccionar Embarque / B/L*", list(dict_ops.keys()))
            monto = st.number_input("Monto a Cobrar ($)*", min_value=0.0, step=50.0)
            concepto = st.text_input("Concepto / Servicio", value="Flete Marítimo y Gastos de Puerto")
            vencimiento = st.date_input("Fecha Límite de Pago", date.today())
            
            if st.form_submit_button("Registrar Cobro", use_container_width=True):
                if monto > 0:
                    supabase.table("cobros").insert({
                        "operacion_id": dict_ops[op_sel],
                        "monto": monto,
                        "concepto": concepto,
                        "fecha_vencimiento": str(vencimiento)
                    }).execute()
                    st.success("✅ Cobro registrado.")
                    st.rerun()
                else:
                    st.error("El monto debe ser mayor a 0.")

st.subheader("⚠️ Pendientes por Cobrar")
cobros_pendientes = supabase.table("cobros").select("*, operaciones(referencia)").eq("pagado", False).order("fecha_vencimiento").execute().data

if cobros_pendientes:
    for c in cobros_pendientes:
        ref_bl = c['operaciones']['referencia'] if c['operaciones'] else "N/A"
        with st.container():
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"📌 **Embarque:** {ref_bl} | **Monto:** ${c['monto']:,.2f} | **Vence:** {c['fecha_vencimiento']} | *{c['concepto']}*")
            if col_btn.button("✅ Marcar Pagado", key=f"cobro_{c['id']}", use_container_width=True):
                supabase.table("cobros").update({"pagado": True, "fecha_pago": str(date.today())}).eq("id", c['id']).execute()
                st.success("¡Cobro actualizado!")
                st.rerun()
            st.divider()
else:
    st.success("🎉 ¡No hay cobros pendientes!")
