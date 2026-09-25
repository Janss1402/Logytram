# ==========================================
# PROYECTO: LOGYTRAM (Sistema NVOCC Guatemala)
# Versión Definitiva: Conectado 100% a Supabase
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

# Configuración inicial de la página
st.set_page_config(
    page_title="Logytram - Gestión NVOCC y Cuentas por Cobrar",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS personalizados para una interfaz profesional
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
            box-shadow: 0 4px 6px rgba(0, 75, 110, 0.2);
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #00334E;
            box-shadow: 0 6px 8px rgba(0, 75, 110, 0.3);
        }
        button[data-baseweb="tab"] {
            font-size: 17px !important;
            font-weight: 600 !important;
            color: #004B6E !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# --- INICIALIZACIÓN DEL CLIENTE DE SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
  try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)
  except Exception as e:
    st.error(
        "⚠️ Error de configuración: Asegúrate de registrar tus secretos de"
        f" Supabase en Streamlit Cloud (Settings -> Secrets). Detalles: {e}"
    )
    st.stop()


supabase = init_supabase()

# --- CONTROL DE SESIÓN Y LOGIN CON SUPABASE AUTH ---
if "user_session" not in st.session_state:
  st.session_state.user_session = None

if not st.session_state.user_session:
  col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
  with col_l2:
    st.markdown(
        "<div style='text-align: center; margin-top: 30px;'>",
        unsafe_allow_html=True,
    )
    if os.path.exists("logo.png"):
      st.image("logo.png", width=200, use_container_width=False)
    else:
      st.markdown(
          "<h1 style='color: #004B6E;'>🚢 LOGYTRAM</h1>", unsafe_allow_html=True
      )
    st.markdown(
        "<h3>Control de Acceso Seguro</h3><p>Ingrese sus credenciales"
        " registradas en Supabase</p></div>",
        unsafe_allow_html=True,
    )

    with st.form("form_login_seguro"):
      email_input = st.text_input("Correo Electrónico")
      password_input = st.text_input("Contraseña", type="password")
      btn_enviar = st.form_submit_button("Iniciar Sesión")

      if btn_enviar:
        try:
          # Autenticación segura gestionada por Supabase
          response = supabase.auth.sign_in_with_password({
              "email": email_input,
              "password": password_input,
          })
          if response:
            st.session_state.user_session = response
            st.success("¡Inicio de sesión exitoso!")
            st.rerun()
        except Exception as err:
          st.error(
              "⚠️ Credenciales inválidas o usuario no registrado. Por favor"
              f" verifique. ({err})"
          )
  st.stop()  # Detiene la ejecución de la app hasta que el usuario inicie sesión correctamente

# ==========================================
# APLICACIÓN PRINCIPAL (Usuario Autenticado)
# ==========================================

# Encabezado visual de la app
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
  if os.path.exists("logo.png"):
    st.image("logo.png", width=180, use_container_width=False)
  st.markdown(
      "<h2 style='margin: 0; color: #004B6E;'>Sistema Integral de Gestión"
      " NVOCC</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='color: #5F6368; margin: 0;'>Módulo de Expedientes, Invoices"
      " y Cuentas por Cobrar</p>",
      unsafe_allow_html=True,
  )

with col_h2:
  # Botón de cierre de sesión seguro
  if st.button("🚪 Cerrar Sesión"):
    try:
      supabase.auth.sign_out()
    except Exception:
      pass
    st.session_state.user_session = None
    st.rerun()

st.markdown("---")

# PARÁMETRO GLOBAL FINANCIERO (Tipo de Cambio)
with st.container():
  st.markdown(
      "<div"
      " style='background: #E8F0FE; padding: 12px 20px; border-radius: 8px;"
      " margin-bottom: 20px; border-left: 5px solid #004B6E;'><b>💱 Parámetro"
      " Financiero Global:</b> Configuración del Tipo de Cambio del Día</div>",
      unsafe_allow_html=True,
  )
  col_tc1, col_tc2, _ = st.columns([1, 1, 2])
  with col_tc1:
    tipo_cambio = st.number_input(
        "Tipo de Cambio (Quetzales por $1 USD)",
        min_value=1.0000,
        value=7.8500,
        format="%.4f",
        key="global_tc",
    )
  with col_tc2:
    st.markdown(
        f"<br><b>1 USD = Q. {tipo_cambio:.4f}</b>", unsafe_allow_html=True
    )

st.markdown("---")

# NAVEGACIÓN POR PESTAÑAS PRINCIPALES DEL SISTEMA
pestanas = st.tabs([
    "📦 Embarques",
    "🏢 Clientes y Cobros (Invoices)",
    "📱 Seguimiento",
    "⏳ Demoras",
    "📄 Cotizaciones",
    "📊 Reportes",
    "💸 Pagos Proveedores",
])

# Renderizado seguro pasando la conexión activa de Supabase a tus módulos
with pestanas[0]:
  embarques.render(tipo_cambio, supabase)
with pestanas[1]:
  cobros.render(tipo_cambio, supabase)
with pestanas[2]:
  seguimiento.render(supabase)
with pestanas[3]:
  demoras.render(supabase)
with pestanas[4]:
  cotizaciones.render(tipo_cambio, supabase)
with pestanas[5]:
  reportes.render(supabase)
with pestanas[6]:
  pagos.render(tipo_cambio, supabase)
