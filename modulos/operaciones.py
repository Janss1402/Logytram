import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

st.set_page_config(page_title="Operaciones", page_icon="🚢", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor inicia sesión en la página principal.")
    st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("🚢 Registro de Embarques y Viajes")

contactos_res = supabase.table("contactos").select("id, nombre_empresa").eq("tipo", "Cliente").execute().data
dict_clientes = {c['nombre_empresa']: c['id'] for c in contactos_res} if contactos_res else {}

with st.expander("➕ ABRIR NUEVO EMBARQUE / OPERACIÓN", expanded=False):
    if not dict_clientes:
        st.warning("⚠️ Primero registra al menos un Cliente en la sección 'Directorio'.")
    else:
        with st.form("form_operacion"):
            ref = st.text_input("Número de Referencia / B/L / Buque*", placeholder="Ej: BL-98012 o MSC ISABEL")
            cliente_sel = st.selectbox("Cliente*", list(dict_clientes.keys()))
            origen = st.text_input("Puerto Origen", placeholder="Ej: Shanghai, China")
            destino = st.text_input("Puerto Destino", placeholder="Ej: Manzanillo, México")
            fecha_emb = st.date_input("Fecha de Embarque", date.today())
            estado = st.selectbox("Estado del Viaje", ["Registrado", "En Tránsito", "En Puerto", "Completado"])

            if st.form_submit_button("Crear Embarque", use_container_width=True):
                if ref:
                    supabase.table("operaciones").insert({
                        "referencia": ref,
                        "cliente_id": dict_clientes[cliente_sel],
                        "puerto_origen": origen,
                        "puerto_destino": destino,
                        "estado": estado,
                        "fecha_embarque": str(fecha_emb)
                    }).execute()
                    st.success("✅ Embarque registrado.")
                    st.rerun()
                else:
                    st.error("Ingresa la referencia o B/L.")

st.subheader("Viajes Registrados")
ops_data = supabase.table("operaciones").select("*, contactos(nombre_empresa)").order("created_at", desc=True).execute().data
if ops_data:
    df_o = pd.DataFrame(ops_data)
    df_o['Cliente'] = df_o['contactos'].apply(lambda x: x['nombre_empresa'] if x else 'N/A')
    df_o_view = df_o[["referencia", "Cliente", "puerto_origen", "puerto_destino", "estado", "fecha_embarque"]]
    df_o_view.columns = ["Ref / BL", "Cliente", "Origen", "Destino", "Estado", "Fecha Embarque"]
    st.dataframe(df_o_view, use_container_width=True)
else:
    st.info("No hay operaciones registradas.")
