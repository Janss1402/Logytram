import pandas as pd
import streamlit as st


def render(supabase):
  st.subheader("👥 Directorio y Gestión de Clientes")

  # 1. Cargar la lista actualizada de clientes desde Supabase
  try:
    response = (
        supabase.table("clientes").select("*").order("nombre").execute()
    )
    raw_clientes = response.data if response.data else []
  except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    raw_clientes = []

  # 2. Organización por Pestañas
  tab_lista, tab_crear, tab_editar = st.tabs([
      "📋 Clientes Registrados",
      "➕ Nuevo Cliente",
      "✏️ Modificar / Eliminar Cliente",
  ])

  # -------------------------------------------------------------
  # PESTAÑA 1: VER CLIENTES REGISTRADOS
  # -------------------------------------------------------------
  with tab_lista:
    if not raw_clientes:
      st.info("No hay clientes registrados en el sistema.")
    else:
      df_clientes = pd.DataFrame(raw_clientes)

      # Mapeo seguro de columnas
      cols_deseadas = ["nombre", "nit", "telefono", "email", "direccion"]
      cols_existentes = [c for c in cols_deseadas if c in df_clientes.columns]

      df_mostrar = df_clientes[cols_existentes].copy()
      nombres_columnas = {
          "nombre": "Nombre / Razón Social",
          "nit": "NIT",
          "telefono": "Teléfono",
          "email": "Correo Electrónico",
          "direccion": "Dirección",
      }
      df_mostrar.rename(columns=nombres_columnas, inplace=True)

      st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

  # -------------------------------------------------------------
  # PESTAÑA 2: AGREGAR UN NUEVO CLIENTE
  # -------------------------------------------------------------
  with tab_crear:
    st.markdown("#### Registrar Nuevo Cliente")
    with st.form("form_nuevo_cliente", clear_on_submit=True):
      col1, col2 = st.columns(2)
      with col1:
        nombre = st.text_input("Nombre de la Empresa / Cliente *")
        nit = st.text_input("NIT")
        telefono = st.text_input("Teléfono")
      with col2:
        email = st.text_input("Correo Electrónico")
        direccion = st.text_input("Dirección")

      submit_cliente = st.form_submit_button("💾 Guardar Cliente")

      if submit_cliente:
        if nombre.strip():
          try:
            nuevo_data = {
                "nombre": nombre.strip(),
                "nit": nit.strip(),
                "telefono": telefono.strip(),
                "email": email.strip(),
                "direccion": direccion.strip(),
            }
            supabase.table("clientes").insert(nuevo_data).execute()
            st.success(f"Cliente '{nombre}' guardado exitosamente.")
            st.rerun()
          except Exception as e:
            st.error(f"Error al guardar el cliente: {e}")
        else:
          st.warning("El campo 'Nombre' es obligatorio.")

  # -------------------------------------------------------------
  # PESTAÑA 3: MODIFICAR O ELIMINAR CLIENTE
  # -------------------------------------------------------------
  with tab_editar:
    st.markdown("#### Editar o Eliminar Registro de Cliente")
    if not raw_clientes:
      st.info("No hay clientes disponibles para modificar o borrar.")
    else:
      # Construcción de opciones para el selector
      dict_clientes = {
          f"{c.get('nombre', 'Sin Nombre')} | NIT: {c.get('nit', 'N/A')}": c
          for c in raw_clientes
      }

      cliente_sel = st.selectbox(
          "Seleccione el cliente a gestionar:",
          options=list(dict_clientes.keys()),
          key="select_cliente_editar",
      )
      cliente_actual = dict_clientes[cliente_sel]

      with st.form("form_editar_eliminar_cliente"):
        st.caption(
            "Modifique los campos necesarios y seleccione la acción a realizar:"
        )
        col_e1, col_e2 = st.columns(2)

        with col_e1:
          e_nombre = st.text_input(
              "Nombre / Razón Social *", value=cliente_actual.get("nombre", "")
          )
          e_nit = st.text_input(
              "NIT", value=cliente_actual.get("nit", "") or ""
          )
          e_telefono = st.text_input(
              "Teléfono", value=cliente_actual.get("telefono", "") or ""
          )

        with col_e2:
          e_email = st.text_input(
              "Correo Electrónico",
              value=cliente_actual.get("email", "") or "",
          )
          e_direccion = st.text_input(
              "Dirección", value=cliente_actual.get("direccion", "") or ""
          )

        st.markdown("---")
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
          btn_actualizar = st.form_submit_button("💾 Actualizar Datos")
        with c_btn2:
          btn_eliminar = st.form_submit_button(
              "🗑️ ELIMINAR CLIENTE PERMANENTEMENTE"
          )

        if btn_actualizar:
          if e_nombre.strip():
            try:
              up_data = {
                  "nombre": e_nombre.strip(),
                  "nit": e_nit.strip(),
                  "telefono": e_telefono.strip(),
                  "email": e_email.strip(),
                  "direccion": e_direccion.strip(),
              }
              supabase.table("clientes").update(up_data).eq(
                  "id", cliente_actual["id"]
              ).execute()
              st.success("Cliente actualizado correctamente.")
              st.rerun()
            except Exception as e:
              st.error(f"Error al actualizar el cliente: {e}")
          else:
            st.warning("El campo 'Nombre' no puede quedar vacío.")

        if btn_eliminar:
          try:
            supabase.table("clientes").delete().eq(
                "id", cliente_actual["id"]
            ).execute()
            st.success(
                f"Cliente '{cliente_actual.get('nombre')}' eliminado del"
                " sistema."
            )
            st.rerun()
          except Exception as e:
            st.error(
                "No se pudo eliminar el cliente. Si tiene facturas o pagos"
                " asociados en el sistema, debes borrar esos registros primero"
                f" para mantener la integridad de los datos. Detalle: {e}"
            )
