import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Directorio", page_icon="👥", layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor inicia sesión en la página principal.")
    st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("👥 Directorio de Contactos")

with st.expander("➕ AGREGAR NUEVO CONTACTO", expanded=False):
    with st.form("form_contacto"):
        nombre = st.text_input("Nombre de la Empresa o Cliente*")
        contacto = st.text_input("Persona de Atención / Contacto")
        tel = st.text_input("Teléfono / WhatsApp")
        tipo = st.selectbox("Categoría*", ["Cliente", "Naviera", "Transportista Terrestre", "Agente de Aduanas", "Otro"])
        
        if st.form_submit_button("Guardar Contacto", use_container_width=True):
            if nombre:
                supabase.table("contactos").insert({
                    "nombre_empresa": nombre,
                    "persona_contacto": contacto,
                    "telefono": tel,
                    "tipo": tipo
                }).execute()
                st.success("✅ Contacto guardado correctamente.")
                st.rerun()
            else:
                st.error("El nombre de la empresa es obligatorio.")

st.subheader("Lista de Contactos Guardados")
data_contactos = supabase.table("contactos").select("*").order("nombre_empresa").execute().data
if data_contactos:
    df_cont = pd.DataFrame(data_contactos)[["nombre_empresa", "persona_contacto", "telefono", "tipo"]]
    df_cont.columns = ["Empresa / Cliente", "Contacto", "Teléfono", "Categoría"]
    st.dataframe(df_cont, use_container_width=True)
else:
    st.info("No hay contactos guardados todavía.")
