import streamlit as st
import pandas as pd
import json
from datetime import datetime

# --- Configuración de la página ---
st.set_page_config(
    layout="wide",
    page_title="Análisis de Partidos",
    page_icon=":soccer:"
)

DATA_FILE = "data.json"

# --- Funciones de Carga de Datos ---
@st.cache_data(show_spinner="Cargando datos...")
def load_data_from_file():
    """Carga los datos de partidos desde el archivo data.json."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"upcoming_matches": [], "finished_matches": []}

    # Asegurarse de que los datos son listas
    upcoming = data.get("upcoming_matches", [])
    finished = data.get("finished_matches", [])
    
    return {
        "upcoming_matches": upcoming if isinstance(upcoming, list) else [],
        "finished_matches": finished if isinstance(finished, list) else [],
    }

# --- Renderizado de la Aplicación ---
def run_main_page():
    """Renderiza la página principal de la aplicación Streamlit."""
    
    st.title("Panel de Partidos")
    st.caption("Esta aplicación muestra los partidos próximos y finalizados desde el archivo `data.json`.")

    # Cargar datos
    data = load_data_from_file()
    upcoming = data.get("upcoming_matches", [])
    finished = data.get("finished_matches", [])

    # --- Métricas Principales ---
    try:
        updated_dt = datetime.fromtimestamp(DATA_FILE.stat().st_mtime).astimezone()
        update_time = updated_dt.strftime("%d/%m %H:%M:%S")
    except FileNotFoundError:
        update_time = "No encontrado"

    kpi_cols = st.columns(3)
    kpi_cols[0].metric("Próximos Partidos", len(upcoming))
    kpi_cols[1].metric("Partidos Finalizados", len(finished))
    kpi_cols[2].metric("Última Actualización del JSON", update_time)

    st.info(
        "Para actualizar los datos, ejecuta el script en la carpeta `manual_updater` en tu ordenador local "
        "y sube el archivo `data.json` actualizado al repositorio."
    )

    st.divider()

    # --- Pestañas de Partidos ---
    tab_upcoming, tab_finished = st.tabs([
        f"📅 Próximos ({len(upcoming)})",
        f"🏁 Finalizados ({len(finished)})",
    ])

    with tab_upcoming:
        st.header("Próximos Partidos")
        if upcoming:
            df_upcoming = pd.DataFrame(upcoming)
            # Selección de columnas para mostrar
            cols_to_show = ['time', 'home_team', 'away_team', 'handicap', 'goal_line']
            st.dataframe(df_upcoming[cols_to_show], use_container_width=True)
        else:
            st.warning("No hay próximos partidos para mostrar.")

    with tab_finished:
        st.header("Partidos Finalizados")
        if finished:
            df_finished = pd.DataFrame(finished)
            # Selección de columnas para mostrar
            cols_to_show = ['time', 'home_team', 'away_team', 'score', 'handicap', 'goal_line']
            st.dataframe(df_finished[cols_to_show], use_container_width=True)
        else:
            st.warning("No hay partidos finalizados para mostrar.")

if __name__ == "__main__":
    run_main_page()