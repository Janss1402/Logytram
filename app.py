# ==========================================
# PROYECTO: LOGYTRAM (Sistema NVOCC Guatemala)
# Versión con Enrutamiento Lineal en Sidebar
# ==========================================
import os
import streamlit as st
from supabase import Client, create_client

# Configuración inicial de la página
st.set_page_config(
    page_title="Logytram - Gestión NVOCC y Cuentas por Cobrar",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS
st.markdown(
    """
    <style>
        .main {
            background-color: #F4F6F9;
            font-family: 'Roboto', sans-serif;
        }
        h1, h2, h3 {
            color: #004B6E !important;
            font-weight: 700;
        }
        div.stButton > button {
            background-color: #004B6E;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 8px;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #00334E;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# --- INICIALIZACIÓN DE SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_supabase()

# --- CONTROL DE SESIÓN ---
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if not st.session_state.autenticado:
  col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
  with col_l2:
    st.markdown(
        "<div style='text-align: center; margin-top: 40px;'>",
        unsafe_allow_html=True,
    )
    if os.path.exists("logo.png"):
      st.image("logo.png", width=200, use_container_width=False)
    else:
      st.markdown(
          "<h1 style='color: #004B6E;'>🚢 LOGYTRAM</h1>", unsafe_allow_html=True
      )
    st.markdown(
        "<h3>Control de Acceso Seguro</h3><p>Inicie sesión con sus"
        " credenciales de Supabase</p></div>",
        unsafe_allow_html=True,
    )

    with st.form("form_login_seguro"):
      email_input = st.text_input("Correo Electrónico")
      password_input = st.text_input("Contraseña", type="password")
      btn_enviar = st.form_submit_button("Iniciar Sesión")

      if btn_enviar:
        try:
          response = supabase.auth.sign_in_with_password({
              "email": email_input,
              "password": password_input,
          })
          if response:
            st.session_state.autenticado = True
            st.session_state.usuario_email = email_input
            st.success("¡Inicio de sesión exitoso!")
            st.rerun()
        except Exception as err:
          st.error(f"⚠️ Credenciales inválidas: {err}")
  st.stop()

# ==========================================
# APLICACIÓN PRINCIPAL (Usuario Autenticado)
# ==========================================

from modulos import cobros, directorio, operaciones, pagos

# Barra lateral de control y navegación lineal
with st.sidebar:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=150)
  st.markdown(f"**Usuario:** {st.session_state.get('usuario_email', 'Admin')}")
  st.markdown("---")

  # Parámetro Global Financiero
  tipo_cambio = st.number_input(
      "Tipo de Cambio (Q por $1 USD)",
      min_value=1.0000,
      value=7.8500,
      format="%.4f",
  )

  st.markdown("---")
  st.markdown("### Navegación del Sistema")
  menu = st.radio(
      "Seleccione un módulo:",
      ["🏢 Cobros e Invoices", "📂 Directorio", "⚙️ Operaciones", "💸 Pagos"],
  )

  st.markdown("---")
  if st.button("🚪 Cerrar Sesión"):
    try:
      supabase.auth.sign_out()
    except Exception:
      pass
    st.session_state.autenticado = False
    st.session_state.usuario_email = None
    st.rerun()

# Encabezado visual principal
st.markdown(
    "<h2 style='color: #004B6E; margin-bottom: 0;'>Sistema Integral de Gestión"
    " NVOCC</h2>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Renderizado condicional lineal por módulo (Evita errores de enrutamiento)
if menu == "🏢 Cobros e Invoices":
  cobros.render(tipo_cambio, supabase)
elif menu == "📂 Directorio":
  directorio.render(supabase)
elif menu == "⚙️ Operaciones":
  operaciones.render(tipo_cambio, supabase)
elif menu == "💸 Pagos":
  pagos.render(tipo_cambio, supabase)
