# ==========================================
# PROYECTO: LOGYTRAM (Sistema NVOCC Guatemala)
# Gestión por Expedientes de Clientes, Invoices y Pagos
# ==========================================
import os
import sqlite3
import streamlit as st

from modulos import (
    cobros,
    cotizaciones,
    demoras,
    embarques,
    pagos,
    reportes,
    seguridad,
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


def inicializar_base_maestra():
  conexion = sqlite3.connect("logytram.db")
  cursor = conexion.cursor()

  # 1. Bitácora de Auditoría
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            accion TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  # 2. Tabla maestra de Clientes (Expedientes por Cliente)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            nit TEXT,
            contacto TEXT,
            telefono TEXT,
            email TEXT,
            direccion TEXT
        )
    """)

  # 3. Tabla de Invoices / Facturas de Cobro por Cliente
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            num_factura TEXT UNIQUE,
            hbl_asociado TEXT,
            fecha_emision TEXT,
            monto_total REAL,
            moneda TEXT,
            estado TEXT, -- Pendiente, Parcial, Pagada
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)

  # 4. Tabla de Pagos / Abonos acreditados a Invoices
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            fecha_pago TEXT,
            monto_abonado REAL,
            metodo_pago TEXT,
            referencia_banco TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )
    """)

  # 5. Tabla base de Embarques
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS embarques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hbl TEXT UNIQUE
        )
    """)

  # Auto-migración segura de columnas en embarques
  columnas_necesarias = {
      "mbl": "TEXT",
      "cliente": "TEXT",
      "tipo_carga": "TEXT",
      "naviera": "TEXT",
      "puerto_destino": "TEXT",
      "estado": "TEXT",
  }

  for col, tipo in columnas_necesarias.items():
    try:
      cursor.execute(f"ALTER TABLE embarques ADD COLUMN {col} {tipo}")
    except sqlite3.OperationalError:
      pass

  # 6. Tabla de Gastos Operativos por Carga / HBL
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_embarque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hbl TEXT,
            concepto TEXT,
            moneda TEXT,
            monto REAL
        )
    """)

  conexion.commit()
  conexion.close()


inicializar_base_maestra()

# ENCABEZADO CENTRADO
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
        Sistema Integral de Gestión NVOCC y Cuentas por Cobrar
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
    "🛡️ Seguridad",
])

with pestanas[0]:
  embarques.render(tipo_cambio)
with pestanas[1]:
  cobros.render(tipo_cambio)
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
with pestanas[7]:
  seguridad.render()
