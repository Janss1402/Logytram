# ==========================================
# PROYECTO: LOGYTRAM (Sistema NVOCC Guatemala)
# Conectado a Supabase (Auth y Base de Datos)
# ==========================================
import os
import streamlit as st
from supabase import Client, create_client

from modulos import (
    cobros,
    cotizaciones,
    demoras,
    embarques,
    pagos,
    reportes,
    seguimiento,
)

st.set_page_config(
    page_title="Logytram - Gestión NVOCC y Cuentas por Cobrar",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .main {
            background-color: #F4F6F9;
            font-family: 'Roboto', sans-serif;
            font-size: 18px;
        }
        h1, h2, h3 {
            color: #004B6E !important;
            font-weight: 700;
        }
        div.stButton > button {
            background-color: #004B6E;
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 12px 24px;
            border-radius: 10px;
            border: none;
            box-shadow: 0 4px 6px rgba(0, 75, 110, 0.2);
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #00334E;
            box-shadow: 0 6px 8px rgba(0, 75, 110, 0.3);
        }
        button[data-baseweb="tab"] {
            font-size: 18px !important;
            font-weight: 600 !important;
            color: #004B6E !important;
        }
        p, span, label {
            font-size: 17px !important;
            color: #2D3748;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
py_init = None  # Marcador para inicializar el cliente
def init_supabase() -> Client:
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


try:
  supabase = init_supabase()
except Exception as e:
  st.error(
      "⚠️ Error al conectar con Supabase. Verifica tus secretos en Streamlit"
      f" Cloud: {e}"
  )
  st.stop()


# --- SISTEMA DE INICIO DE SESIÓN CON SUPABASE AUTH ---
if "user_session" not in st.session_state:
  st.session_state.user_session = None

if not st.session_state.user_session:
  st.markdown(
      "<div style='text-align: center; margin-top: 40px;'>",
      unsafe_allow_html=True,
  )
  if os.path.exists("logo.png"):
    st.image("logo.png", width=220, use_container_width=False)
  else:
    st.markdown(
        "<h1 style='color: #004B6E;'>🚢 LOGYTRAM</h1>", unsafe_allow_html=True
    )
  st.markdown(
      "<h3>Iniciar Sesión - Supabase Auth</h3></div>", unsafe_allow_html=True
  )

  col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
  with col_l2:
    with st.form("form_login_supabase"):
      email_input = st.text_input("Correo Electrónico (Email)")
      password_input = st.text_input("Contraseña", type="password")
      submit_login = st.form_submit_button("Entrar al Sistema")

      if submit_login:
        try:
          # Intento de autenticación directa con Supabase Auth
          response = supabase.auth.sign_in_with_password({
              "email": email_input,
              "password": password_input,
          })
          if response:
            st.session_state.user_session = response
            st.success("¡Acceso exitoso!")
            st.rerun()
        except Exception as err:
          st.error(
              "⚠️ Credenciales incorrectas o usuario no registrado en"
              f" Supabase. Detalle: {err}"
          )
  st.stop()


# --- APLICACIÓN PRINCIPAL (Una vez logueado con Supabase) ---

st.markdown(
    "<div style='text-align: center; margin-top: 10px; margin-bottom: 10px;'>",
    unsafe_allow_html=True,
)
if os.path.exists("logo.png"):
  st.image("logo.png", width=240, use_container_width=False)
else:
  st.markdown(
      "<h1 style='color: #004B6E;'>🚢 LOGYTRAM</h1>", unsafe_allow_html=True
  )

st.markdown(
    """
    <p style='font-size: 20px; color: #5F6368; font-weight: 500; margin-top: 5px;'>
        Sistema Integral de Gestión NVOCC y Cuentas por Cobrar (Supabase Active)
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# PARÁMETRO GLOBAL DE TIPO DE CAMBIO
with st.container():
  st.markdown(
      "<div"
      " style='background: #E8F0FE; padding: 10px 20px; border-radius: 8px;"
      " margin-bottom: 20px; border-left: 5px solid #004B6E;'><b>💱 Parámetro"
      " Financiero Global:</b> Configuración del Tipo de Cambio del Día</div>",
      unsafe_allow_html=True,
  )
  col_tc1, col_tc2, col_tc3 = st.columns([1, 1, 2])
  with col_tc1:
    tipo_cambio = st.number_input(
        "Tipo de Cambio (Q por $1 USD)",
        min_value=1.0000,
        value=7.8500,
        format="%.4f",
        key="global_tc",
    )
  with col_tc2:
    st.markdown(
        "<br><b>1 USD = Q. " + str(tipo_cambio) + "</b>", unsafe_allow_html=True
    )

st.markdown("---")

# NAVEGACIÓN POR PESTAÑAS PRINCIPALES
pestanas = st.tabs([
    "📦 Embarques",
    "🏢 Clientes y Cobros (Invoices)",
    "📱 Seguimiento",
    "⏳ Demoras",
    "📄 Cotizaciones",
    "📊 Reportes",
    "💸 Pagos Proveedores",
])

with pestanas[0]:
  embarques.render(tipo_cambio, supabase)  # Opcional si tus módulos usan supabase
with pestanas[1]:
  cobros.render(tipo_cambio, supabase)
with pestanas[2]:
  seguimiento.render()
with pestanas[3]:
  demoras.render()
with pestanas[4]:
  cotizaciones.render(tipo_cambio)
with pestanas[5]:
  reportes.render()
with pestanas[6]:
  pagos.render(tipo_cambio)
