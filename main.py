import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora de Notas Cloud", layout="wide", page_icon="🎓")

# --- CONEXIÓN A SUPABASE ---
# Asegúrate de tener estas llaves en .streamlit/secrets.toml
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("⚠️ Error: No se encontraron las credenciales de Supabase en los secretos.")
    st.stop()

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_ramos_db(usuario):
    """Trae todos los ramos de un usuario desde Supabase"""
    res = supabase.table("notas_ramos").select("*").eq("usuario", usuario).execute()
    # Formato: { 'NombreRamo': [lista_de_notas] }
    return {row['ramo']: row['datos'] for row in res.data}

def guardar_ramo_db(usuario, ramo, datos):
    """Guarda o actualiza un ramo específico"""
    supabase.table("notas_ramos").upsert({
        "usuario": usuario,
        "ramo": ramo,
        "datos": datos
    }, on_conflict="usuario,ramo").execute()

def eliminar_ramo_db(usuario, ramo):
    """Borra un ramo de la base de datos"""
    supabase.table("notas_ramos").delete().eq("usuario", usuario).eq("ramo", ramo).execute()

# --- ESTADO DE LA SESIÓN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = "invitado"

if 'ramos' not in st.session_state:
    st.session_state.ramos = cargar_ramos_db(st.session_state.usuario)

if 'ramo_sel' not in st.session_state:
    st.session_state.ramo_sel = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👨‍🎓 Mis Ramos")
    
    # Identificación de usuario
    user_input = st.text_input("Tu Usuario (para guardar tus datos):", value=st.session_state.usuario)
    if user_input != st.session_state.usuario:
        st.session_state.usuario = user_input
        st.session_state.ramos = cargar_ramos_db(user_input)
        st.rerun()

    st.divider()
    
    # Añadir Ramo
    with st.expander("➕ Añadir Nuevo Ramo"):
        nuevo = st.text_input("Nombre del ramo:").strip()
        if st.button("Crear"):
            if nuevo and nuevo not in st.session_state.ramos:
                st.session_state.ramos[nuevo] = []
                st.session_state.ramo_sel = nuevo
                guardar_ramo_db(st.session_state.usuario, nuevo, [])
                st.rerun()

    st.write("### Selecciona un Ramo:")
    for r in list(st.session_state.ramos.keys()):
        # Botones que actúan como labels
        if st.button(f"📘 {r}", key=f"btn_{r}", use_container_width=True):
            st.session_state.ramo_sel = r
            st.rerun()

# --- CUERPO PRINCIPAL ---
if st.session_state.ramo_sel:
    ramo_actual = st.session_state.ramo_sel
    st.title(f"Editando: {ramo_actual}")
    
    # Cargar datos del ramo seleccionado
    data = st.session_state.ramos[ramo_actual]
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["Evaluación", "Nota", "Ponderación %"])

    st.info("💡 Edita las celdas y presiona el botón inferior para guardar y calcular.")

    # EDITOR DE DATOS
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "Nota": st.column_config.NumberColumn(min_value=1.0, max_value=7.0, format="%.1f", step=0.1),
            "Ponderación %": st.column_config.NumberColumn(min_value=0, max_value=100, step=1)
        },
        use_container_width=True,
        key="main_editor"
    )

    # ACCIONES
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Guardar y Calcular", type="primary"):
            # Guardamos en Session State y en Supabase
            lista_final = edited_df.to_dict('records')
            st.session_state.ramos[ramo_actual] = lista_final
            guardar_ramo_db(st.session_state.usuario, ramo_actual, lista_final)
            st.toast("¡Sincronizado con la nube!", icon="☁️")
            st.rerun()
    with col2:
        if st.button("🗑️ Eliminar Ramo"):
            eliminar_ramo_db(st.session_state.usuario, ramo_actual)
            del st.session_state.ramos[ramo_actual]
            st.session_state.ramo_sel = None
            st.rerun()

    # --- CÁLCULOS CHILENOS (1.0 - 7.0) ---
    if not edited_df.empty:
        try:
            notas = pd.to_numeric(edited_df["Nota"])
            pesos = pd.to_numeric(edited_df["Ponderación %"])
            
            suma_ponderada = (notas * (pesos / 100)).sum()
            total_peso = pesos.sum()
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Nota Actual", f"{suma_ponderada:.2f}")
            m2.metric("Avance Ramo", f"{total_peso}%")

            if total_peso < 100:
                faltante = 100 - total_peso
                necesaria = (4.0 - suma_ponderada) / (faltante / 100)
                m3.metric("Necesitas un para el 4.0", f"{max(necesaria, 1.0):.2f}")
                
                if necesaria > 7.0:
                    st.error(f"⚠️ Necesitas un **{necesaria:.2f}** para pasar. ¡A ponerle ganas!")
                elif necesaria <= 1.0:
                    st.success("🎉 ¡Ya pasaste el ramo!")
                else:
                    st.warning(f"Necesitas promediar un **{necesaria:.2f}** en el {faltante}% restante.")
            elif total_peso == 100:
                if suma_ponderada >= 3.95:
                    st.balloons()
                    st.success("¡APROBADO! 🥳")
                else:
                    st.error("Reprobado. ¡A darlo todo en el examen!")
        except:
            st.warning("Completa todas las notas para ver el cálculo.")
else:
    st.title("Bienvenido 🎓")
    st.write("Selecciona un ramo a la izquierda para comenzar.")