import os
from datetime import datetime
import pytz
import streamlit as st

LOGO_PATH = "assets/logo.png"


def aplicar_estilos_azul_marino():
  st.markdown(
      """
        <style>
        /* Estilos Generales Azul Marino (Navy Blue) */
        .stApp {
            background-color: #f8fafc;
        }
        
        /* Barra Lateral (Sidebar) Azul Marino */
        [data-testid="stSidebar"] {
            background-color: #0b192c !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] * {
            color: #f1f5f9 !important;
        }
        
        /* Banner Header Principal */
        .main-header {
            background: linear-gradient(135deg, #0b192c 0%, #1e3e62 100%);
            padding: 1.4rem;
            border-radius: 12px;
            border-left: 8px solid #008bce;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
            margin-bottom: 1.5rem;
        }
        .banner-title {
            color: #ffffff !important;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: 0.5px;
        }
        .banner-subtitle {
            color: #cbd5e1 !important;
            font-size: 0.95rem;
            margin-top: 0.3rem;
        }

        /* Botones en Tono Azul Marino */
        .stButton > button {
            background-color: #1e3e62 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background-color: #008bce !important;
            color: #ffffff !important;
            box-shadow: 0 4px 10px rgba(0, 139, 206, 0.3);
        }

        /* Pestañas (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #e2e8f0;
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
            color: #0b192c;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #0b192c !important;
            color: #ffffff !important;
        }
        
        /* Métricas e Indicadores de Saldo */
        [data-testid="stMetricValue"] {
            color: #0b192c !important;
            font-weight: bold !important;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )


def render_banner():
  aplicar_estilos_azul_marino()

  # Muestra el logo en la parte superior de la Barra Lateral si existe
  if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)
    st.sidebar.markdown("---")

  # Hora oficial de Guatemala
  tz_gt = pytz.timezone("America/Guatemala")
  hora_gt = datetime.now(tz_gt).strftime("%d/%m/%Y | %I:%M:%S %p")

  col_logo, col_info = st.columns([1, 4])

  with col_logo:
    if os.path.exists(LOGO_PATH):
      st.image(LOGO_PATH, width=140)
    else:
      st.markdown("### 🚢 **LOGYTRAM**")

  with col_info:
    st.markdown(
        f"""
        <div class="main-header">
            <div class="banner-title">LOGYTRAM - Sistema de Control de Cuentas</div>
            <div class="banner-subtitle">📍 Guatemala | 🕒 {hora_gt} (Hora Oficial GT)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def gestion_personalizacion():
  st.subheader("🎨 Personalización de Marca (Logytram)")
  st.write(
      "Sube el logo de tu empresa. Se mostrará en el menú lateral, en la"
      " pantalla principal y en los PDF de Estado de Cuenta."
  )

  os.makedirs("assets", exist_ok=True)

  uploaded_logo = st.file_uploader(
      "Selecciona tu logo (PNG o JPG)", type=["png", "jpg", "jpeg"]
  )
  if uploaded_logo is not None:
    with open(LOGO_PATH, "wb") as f:
      f.write(uploaded_logo.getbuffer())
    st.success("Logo actualizado correctamente.")
    st.rerun()

  if os.path.exists(LOGO_PATH):
    st.markdown("**Logo guardado en el sistema:**")
    st.image(LOGO_PATH, width=160)
    if st.button("Eliminar Logo"):
      os.remove(LOGO_PATH)
      st.success("Logo eliminado.")
      st.rerun()
