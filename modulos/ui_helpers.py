import os
from datetime import datetime
import pytz
import streamlit as st

LOGO_PATH = "assets/logo.png"


def cargar_css_personalizado():
  st.markdown(
      """
        <style>
        .main-header {
            background-color: #0e1117;
            padding: 1.2rem;
            border-radius: 10px;
            border-left: 6px solid #1f77b4;
            margin-bottom: 1.5rem;
        }
        .banner-title {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: bold;
            margin: 0;
        }
        .banner-subtitle {
            color: #a0aab2;
            font-size: 0.95rem;
            margin-top: 0.2rem;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )


def render_banner():
  cargar_css_personalizado()

  # Hora oficial Guatemala (America/Guatemala UTC-6)
  tz_gt = pytz.timezone("America/Guatemala")
  hora_gt = datetime.now(tz_gt).strftime("%d/%m/%Y | %I:%M:%S %p")

  col_logo, col_info = st.columns([1, 4])

  with col_logo:
    if os.path.exists(LOGO_PATH):
      st.image(LOGO_PATH, width=130)
    else:
      st.markdown("### 📦 **LOGYTRAM**")

  with col_info:
    st.markdown(
        f"""
        <div class="main-header">
            <div class="banner-title">LOGYTRAM - Sistema de Cuentas por Cobrar</div>
            <div class="banner-subtitle">📍 Guatemala | 🕒 {hora_gt} (Hora Oficial GT)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def gestion_personalizacion():
  st.subheader("🎨 Personalización de Marca (Logytram)")
  st.write(
      "Sube el logo de tu empresa. Se mostrará en el banner del sistema y en"
      " todos los reportes PDF de Estado de Cuenta."
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
    st.markdown("**Logo actual:**")
    st.image(LOGO_PATH, width=150)
    if st.button("Eliminar Logo"):
      os.remove(LOGO_PATH)
      st.success("Logo eliminado.")
      st.rerun()
