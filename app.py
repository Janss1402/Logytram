import modulos.backups as backups
import modulos.cobros as cobros
import modulos.directorio as directorio
import modulos.ui_helpers as ui
from supabase import Client, create_client
import streamlit as st

st.set_page_config(
    page_title="LOGYTRAM - Control de cuentas", layout="wide", page_icon="📦"
)


# Inicializar Supabase
@st.cache_resource
def init_supabase():
  url = st.secrets["SUPABASE_URL"]
  key = st.secrets["SUPABASE_KEY"]
  return create_client(url, key)


supabase = init_supabase()

# Login
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False

if not st.session_state.authenticated:
  st.title("🔒 LOGYTRAM - Acceso al Sistema")
  with st.form("login_form"):
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")
    submit = st.form_submit_button("Iniciar Sesión")

    if submit:
      try:
        auth_res = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if auth_res.user:
          st.session_state.authenticated = True
          st.rerun()
      except Exception:
        st.error("Credenciales incorrectas.")
  st.stop()

# --- INTERFAZ Y NAVEGACIÓN ---
ui.render_banner()

st.sidebar.title("Navegación LOGYTRAM")
opcion = st.sidebar.radio(
    "Seleccione un módulo:",
    [
        "💰 Cobros e Invoices",
        "🏢 Directorio de Clientes",
        "⚙️ Personalización y Respaldos",
    ],
)

if st.sidebar.button("Cerrar Sesión"):
  st.session_state.authenticated = False
  st.rerun()

tipo_cambio = 7.80

if opcion == "💰 Cobros e Invoices":
  cobros.render(tipo_cambio, supabase)
elif opcion == "🏢 Directorio de Clientes":
  directorio.render(supabase)
elif opcion == "⚙️ Personalización y Respaldos":
  ui.gestion_personalizacion()
  st.markdown("---")
  backups.render(supabase)
