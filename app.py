import streamlit as st
from supabase import create_client, Client
import modulos.directorio as directorio
import modulos.cobros as cobros

st.set_page_config(page_title="Gestión de Cuentas por Cobrar", layout="wide")

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Login de Supabase Auth
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Acceso al Sistema")
    with st.form("login_form"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")

        if submit:
            try:
                auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if auth_res.user:
                    st.session_state.authenticated = True
                    st.success("Sesión iniciada correctamente")
                    st.rerun()
            except Exception as e:
                st.error("Credenciales incorrectas o problema de conexión.")
    st.stop()

# --- MENÚ PRINCIPAL SIMPLIFICADO ---
st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Seleccione un módulo:",
    ["🏢 Directorio de Clientes", "💰 Cobros e Invoices"]
)

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.authenticated = False
    st.rerun()

tipo_cambio = 7.80  # Tipo de cambio referencial (Q/USD)

if opcion == "🏢 Directorio de Clientes":
    directorio.render(supabase)
elif opcion == "💰 Cobros e Invoices":
    cobros.render(tipo_cambio, supabase)
