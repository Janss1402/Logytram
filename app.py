import os
import streamlit as st
from supabase import Client, create_client

# 1. Configuración de la página (Debe ser el primer comando de Streamlit)
st.set_page_config(page_title="Logytram NVOCC", page_icon="🚢", layout="wide")

# 2. Conexión a Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# 3. Control de Sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #004B6E;'>🚢 LOGYTRAM - Acceso</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("Correo")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar")

            if submit:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res:
                        st.session_state.autenticado = True
                        st.session_state.usuario = email
                        st.rerun()
                except Exception as e:
                    st.error("Credenciales incorrectas.")
    st.stop() # Detiene todo si no hay sesión

# 4. Interfaz Principal (Solo visible si hay sesión)
from modulos import cobros, directorio, operaciones, pagos

with st.sidebar:
    st.markdown(f"**Usuario:** {st.session_state.usuario}")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    
    st.markdown("---")
    tipo_cambio = st.number_input("Tipo de Cambio (Q/$)", value=7.8500, format="%.4f")
    st.markdown("---")
    menu = st.radio("Navegación:", ["Cobros e Invoices", "Directorio", "Operaciones", "Pagos"])

st.title(f"Módulo: {menu}")
st.markdown("---")

# 5. Enrutamiento a los módulos limpios
if menu == "Cobros e Invoices":
    cobros.render(tipo_cambio, supabase)
elif menu == "Directorio":
    directorio.render(supabase)
elif menu == "Operaciones":
    operaciones.render(tipo_cambio, supabase)
elif menu == "Pagos":
    pagos.render(tipo_cambio, supabase)
