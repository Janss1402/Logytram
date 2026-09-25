import os
import streamlit as st
from supabase import Client, create_client
from modulos import cobros, directorio, operaciones, pagos

st.set_page_config(
    page_title="Logytram - Gestión NVOCC", page_icon="🚢", layout="wide"
)

# Inicialización segura de Supabase
@st.cache_resource
def init_supabase() -> Client:
  return create_client(
      st.secrets["supabase"]["url"], st.secrets["supabase"]["key"]
  )


try:
  supabase = init_supabase()
except Exception as e:
  st.error(f"Error de configuración en Supabase: {e}")
  st.stop()

# Control de sesión
if "user_session" not in st.session_state:
  st.session_state.user_session = None

if not st.session_state.user_session:
  col1, col2, col3 = st.columns([1, 1.5, 1])
  with col2:
    st.markdown("<h2 style='text-align: center;'>🚢 LOGYTRAM</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Iniciar Sesión</h4>", unsafe_allow_html=True)
    
    with st.form("login_form"):
      email = st.text_input("Correo electrónico")
      password = st.text_input("Contraseña", type="password")
      submit = st.form_submit_button("Entrar")

      if submit:
        try:
          res = supabase.auth.sign_in_with_password(
              {"email": email, "password": password}
          )
          if res:
            st.session_state.user_session = res
            st.success("¡Bienvenido!")
            st.rerun()
        except Exception as err:
          st.error(f"Credenciales incorrectas: {err}")
  st.stop()

# Aplicación Principal
st.sidebar.title("Menú Principal")
if st.sidebar.button("Cerrar Sesión"):
  supabase.auth.sign_out()
  st.session_state.user_session = None
  st.rerun()

tipo_cambio = st.sidebar.number_input(
    "Tipo de Cambio (Q por $1)", value=7.85, format="%.4f"
)

pestanas = st.tabs(["🏢 Cobros e Invoices", "📂 Directorio", "⚙️ Operaciones", "💸 Pagos"])

with pestanas[0]:
  cobros.render(tipo_cambio, supabase)
with pestanas[1]:
  directorio.render(supabase)
with pestanas[2]:
  operaciones.render(tipo_cambio, supabase)
with pestanas[3]:
  pagos.render(tipo_cambio, supabase)
