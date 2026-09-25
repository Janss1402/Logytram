from datetime import datetime
import json
import streamlit as st


def render(supabase):
  st.subheader("💾 Respaldos y Copias de Seguridad (Backups)")
  st.write(
      "Exporta toda tu información financiera a un archivo seguro o restaura"
      " una copia guardada en caso de emergencia."
  )

  col_exp, col_imp = st.columns(2)

  # --- EXPORTAR BACKUP ---
  with col_exp:
    st.markdown("### 📥 Descargar Backup")
    st.caption("Genera una copia completa de tus clientes, facturas y pagos.")

    if st.button("Generar Copia de Seguridad"):
      try:
        backup_data = {
            "fecha_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "clientes": supabase.table("clientes").select("*").execute().data,
            "invoices": supabase.table("invoices").select("*").execute().data,
            "pagos": supabase.table("pagos").select("*").execute().data,
            "embarques": (
                supabase.table("embarques").select("*").execute().data
            ),
        }

        json_str = json.dumps(backup_data, indent=4, default=str)
        nombre_archivo = f"Logytram_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        st.download_button(
            label="⬇️ Descargar Archivo JSON",
            data=json_str,
            file_name=nombre_archivo,
            mime="application/json",
        )
        st.success("Backup listo para descargar.")
      except Exception as e:
        st.error(f"Error generando backup: {e}")

  # --- RESTAURAR BACKUP ---
  with col_imp:
    st.markdown("### 📤 Cargar / Restaurar Backup")
    st.caption("Sube un archivo `.json` previamente descargado para restaurar.")

    uploaded_backup = st.file_uploader(
        "Seleccionar archivo de respaldo", type=["json"]
    )

    if uploaded_backup is not None:
      if st.button("⚠️ Confirmar Restauración de Datos"):
        try:
          data = json.load(uploaded_backup)

          # Insertar o actualizar registros
          for c in data.get("clientes", []):
            supabase.table("clientes").upsert(c).execute()
          for i in data.get("invoices", []):
            supabase.table("invoices").upsert(i).execute()
          for p in data.get("pagos", []):
            supabase.table("pagos").upsert(p).execute()
          for e in data.get("embarques", []):
            supabase.table("embarques").upsert(e).execute()

          st.success("¡Base de datos restaurada con éxito!")
        except Exception as e:
          st.error(f"Error al restaurar los datos: {e}")
