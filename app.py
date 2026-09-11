import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
import io

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Carga & Logística",
    page_icon="🚢",
    layout="wide"
)

# --- 2. CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 3. MÓDULO DE SEGURIDAD Y LOGIN ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown("
