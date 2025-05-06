import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- Configuración de Página ---
st.set_page_config(
    page_title="Análisis Histórico Juegos Olímpicos",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funciones de Carga de Datos ---

@st.cache_data # Cachea el resultado para mejorar rendimiento
def load_data(filepath='jjoo.csv'):
    """Carga el archivo CSV pre-procesado 'jjoo.csv'."""
    try:
        df = pd.read_csv(filepath)
        # Opcional: Convertir columnas si no se cargan con el tipo correcto
        # df['born_date'] = pd.to_datetime(df['born_date'], errors='coerce')
        # df['year'] = pd.to_numeric(df['year'], errors='coerce')
        # ... etc ...

        # Verificar columnas esenciales (ajusta según necesites)
        essential_cols = ['year', 'type', 'noc', 'medal', 'age', 'gender', 'discipline_grouped', 'name', 'discipline']
        missing_cols = [col for col in essential_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Faltan columnas esenciales en '{filepath}': {', '.join(missing_cols)}")
            return pd.DataFrame()

        st.success(f"Archivo '{filepath}' cargado correctamente ({len(df):,} filas).")
        return df
    except FileNotFoundError:
        st.error(f"Error: El archivo '{filepath}' no se encontró. Asegúrate de que está en el mismo directorio que el script.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar o procesar '{filepath}': {e}")
        return pd.DataFrame()


@st.cache_data
def load_noc_coords(filepath='noc_coordinates.csv'):
    """Carga los datos de coordenadas NOC y el nombre del país."""
    try:
        df_coords = pd.read_csv(filepath)
        # Verificar columnas requeridas
        if 'noc' not in df_coords.columns or 'country' not in df_coords.columns or 'latitude' not in df_coords.columns or 'longitude' not in df_coords.columns:
            st.error(f"El archivo '{filepath}' debe contener columnas 'noc', 'country', 'latitude', 'longitude'.")
            return pd.DataFrame(columns=['noc', 'country', 'latitude', 'longitude'])
        # Asegurar que no haya NaNs en columnas clave
        df_coords.dropna(subset=['noc', 'country', 'latitude', 'longitude'], inplace=True)
        return df_coords[['noc', 'country', 'latitude', 'longitude']]
    except FileNotFoundError:
        st.error(f"Archivo '{filepath}' no encontrado. Asegúrate de que esté en la ruta correcta.")
        return pd.DataFrame(columns=['noc', 'country', 'latitude', 'longitude'])
    except Exception as e:
        st.error(f"Error al cargar o procesar '{filepath}': {e}")
        return pd.DataFrame(columns=['noc', 'country', 'latitude', 'longitude'])

# --- Cargar Datos ---
df_olympics = load_data()
df_coords = load_noc_coords()

# --- Sidebar para Filtros Globales ---
st.sidebar.header("Filtros Globales 🌍")

if df_olympics.empty:
    st.sidebar.error("No se pudieron cargar los datos principales ('jjoo.csv'). La aplicación no puede continuar.")
    # Detener la ejecución si no hay datos
    st.stop()

# --- Filtros ---
# Asegurar que 'year' es numérico antes de usar min/max
if pd.api.types.is_numeric_dtype(df_olympics['year']):
    min_year = int(df_olympics['year'].min())
    max_year = int(df_olympics['year'].max())
    selected_years = st.sidebar.slider(
        "Selecciona Rango de Años",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year) # Por defecto, todo el rango
    )
else:
    st.sidebar.error("La columna 'year' no es numérica o no se cargó correctamente.")
    selected_years = (0, 0) # Valor placeholder inválido

# Filtro por tipo de juego (columna 'type')
if 'type' in df_olympics.columns:
    type_options = ['Todos'] + list(df_olympics['type'].unique())
    selected_type = st.sidebar.radio(
        "Tipo de Juego",
        options=type_options,
        index=0 # 'Todos' por defecto
    )
else:
    st.sidebar.warning("Columna 'type' no encontrada. No se puede filtrar por tipo de juego.")
    selected_type = 'Todos'

# Filtro por género (columna 'gender')
if 'gender' in df_olympics.columns:
    gender_options = list(df_olympics['gender'].unique())
    # Remover NaNs si existen en las opciones
    gender_options = [g for g in gender_options if pd.notna(g)]
    selected_gender = st.sidebar.multiselect(
        "Selecciona Género",
        options=gender_options,
        default=gender_options # Por defecto, todos seleccionados
    )
else:
    st.sidebar.warning("Columna 'gender' no encontrada. No se puede filtrar por género.")
    selected_gender = []

# --- Filtrar el DataFrame Principal ---
df_filtered = df_olympics[
    (df_olympics['year'] >= selected_years[0]) &
    (df_olympics['year'] <= selected_years[1])
]

if selected_type != 'Todos' and 'type' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['type'] == selected_type]

if selected_gender and 'gender' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['gender'].isin(selected_gender)]

# --- Verificar si quedan datos después de filtrar ---
if df_filtered.empty and not df_olympics.empty :
    st.warning("No hay datos disponibles para los filtros seleccionados. Por favor, ajusta los filtros.")
    st.stop() # Detener si no hay datos que mostrar

# --- Título Principal ---
st.title("🏅 Análisis Interactivo de los Juegos Olímpicos Históricos 🏅")
st.markdown(f"Mostrando datos desde **{selected_years[0]}** hasta **{selected_years[1]}**.")
# Mostrar tipo de juego seleccionado si no es 'Todos'
if selected_type != 'Todos':
    st.markdown(f"Tipo de Juego: **{selected_type}**")
st.markdown("---")

# --- Pestañas para organizar el contenido ---
tab_overview, tab_geo, tab_athletes, tab_disciplines = st.tabs([
    "📈 Visión General",
    "🌍 Análisis Geográfico",
    "🧍 Análisis de Atletas",
    "🤸 Análisis por Disciplina"
])

# --- PESTAÑA 1: VISIÓN GENERAL ---
with tab_overview:
    st.header("Tendencias Generales de Participación")

    col1, col2 = st.columns(2)
    with col1:
        # Usar 'name' para atletas únicos
        total_athletes = df_filtered['name'].nunique()
        st.metric("Atletas Únicos", f"{total_athletes:,}")
    with col2:
        # Usar 'noc' para países únicos
        total_countries = df_filtered['noc'].nunique()
        st.metric("Países (NOCs) Participantes", f"{total_countries:,}")

    st.markdown("### Evolución de la Participación por Género")
    if 'year' in df_filtered.columns and 'gender' in df_filtered.columns:
        participation_over_time = df_filtered.groupby(['year', 'gender']).size().reset_index(name='Count')
        fig_participation = px.area(participation_over_time, x='year', y='Count', color='gender',
                                    labels={'year': 'Año', 'Count': 'Número de Participantes', 'gender': 'Género'},
                                    markers=True, template='plotly_white')
        fig_participation.update_layout(hovermode="x unified")
        st.plotly_chart(fig_participation, use_container_width=True)
    else:
        st.warning("Columnas 'year' o 'gender' no disponibles para gráfico de evolución.")

    st.markdown("### Número de Disciplinas por Año")
    if 'year' in df_filtered.columns and 'discipline' in df_filtered.columns:
        # Usar 'discipline' para contar disciplinas únicas
        disciplines_over_time = df_filtered.groupby('year')['discipline'].nunique().reset_index()
        fig_disciplines = px.line(disciplines_over_time, x='year', y='discipline',
                                title="Número de Disciplinas Olímpicas a lo largo del Tiempo",
                                labels={'year': 'Año', 'discipline': 'Número de Disciplinas Únicas'},
                                markers=True, template='plotly_white')
        st.plotly_chart(fig_disciplines, use_container_width=True)
    else:
        st.warning("Columnas 'year' o 'discipline' no disponibles para gráfico de disciplinas.")


# --- PESTAÑA 2: ANÁLISIS GEOGRÁFICO ---
with tab_geo:
    st.header("Rendimiento y Participación por País (NOC)")

    # Calcular métricas por NOC (usando 'noc', 'name', 'medal')
    # Asegurar que 'medal' no contenga solo NaNs o valores inesperados
    df_filtered['medal_present'] = df_filtered['medal'].notna() & (df_filtered['medal'] != 'No Medal') # Ajusta 'No Medal' si usaste otro valor

    metrics_by_noc = df_filtered.groupby('noc').agg(
        Total_Athletes=('name', 'nunique'),
        Total_Medals=('medal_present', 'sum'), # Sumar True (1) donde hay medalla
        # Contar medallas específicas (asegúrate que estos strings coinciden con tus datos)
        Gold=('medal', lambda x: (x == 'Gold').sum()),
        Silver=('medal', lambda x: (x == 'Silver').sum()),
        Bronze=('medal', lambda x: (x == 'Bronze').sum())
    ).reset_index()
    # Convertir Total_Medals a int
    metrics_by_noc['Total_Medals'] = metrics_by_noc['Total_Medals'].astype(int)


    # Añadir opción para ordenar países
    sort_options = ['Total_Medals', 'Total_Athletes', 'Gold', 'Silver', 'Bronze']
    valid_sort_options = [opt for opt in sort_options if opt in metrics_by_noc.columns] # Solo opciones válidas
    if not valid_sort_options:
        st.warning("No se pudieron calcular métricas para ordenar países.")
    else:
        sort_by = st.selectbox("Ordenar países por:", valid_sort_options, key='geo_sort')
        top_n = st.slider("Mostrar Top N Países:", min_value=5, max_value=50, value=15, key='geo_topn')

        top_countries = metrics_by_noc.sort_values(by=sort_by, ascending=False).head(top_n)

        # Gráfico de Barras Top Países
        st.markdown(f"### Top {top_n} Países por {sort_by.replace('_', ' ')}")
        fig_top_countries = px.bar(top_countries, x='noc', y=sort_by,
                                hover_data=['Total_Athletes', 'Gold', 'Silver', 'Bronze'],
                                labels={'noc': 'País (NOC)', sort_by: sort_by.replace('_', ' ')},
                                template='plotly_white',
                                color=sort_by,
                                color_continuous_scale=px.colors.sequential.Plasma)
        st.plotly_chart(fig_top_countries, use_container_width=True)

    # Mapa de Puntos (Scatter Mapbox)
    st.markdown("### Distribución Geográfica de Medallas")
    if not df_coords.empty and 'noc' in metrics_by_noc.columns:
        # Unir métricas con coordenadas (usar 'noc')
        df_map_data = pd.merge(metrics_by_noc[metrics_by_noc['Total_Medals'] > 0], df_coords, on='noc', how='left')
        df_map_data.dropna(subset=['latitude', 'longitude'], inplace=True)

        if not df_map_data.empty:
            fig_scatter_map = px.scatter_mapbox(
                df_map_data,
                lat="latitude",
                lon="longitude",
                size="Total_Medals",
                color="Total_Medals",
                hover_name="country", # Usar 'country' para el nombre principal
                hover_data={
                    "latitude": False, "longitude": False,
                    "noc": True, "country": False, "Total_Medals": True, "Total_Athletes": True,
                    "Gold": True, "Silver": True, "Bronze": True
                },
                color_continuous_scale=px.colors.sequential.Viridis,
                size_max=60,
                zoom=0.8,
                mapbox_style="carto-positron",
                title="Distribución Geográfica de Medallas Totales por NOC"
            )
            fig_scatter_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_scatter_map, use_container_width=True)
        else:
            st.warning("No se pudieron combinar datos de medallas con coordenadas para el mapa.")
    else:
        st.warning("Datos de coordenadas ('noc_coordinates.csv') no cargados o columna 'noc' no encontrada para crear mapa.")

# --- PESTAÑA 3: ANÁLISIS DE ATLETAS ---
with tab_athletes:
    st.header("Características Físicas y Demográficas de los Atletas")

    # Usar nombres de columna de jjoo.csv: 'age', 'height_cm', 'weight_kg'
    numeric_cols = ['age', 'height_cm', 'weight_kg']
    available_numeric_cols = [col for col in numeric_cols if col in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered[col])]

    if not available_numeric_cols:
        st.warning("No hay columnas numéricas ('age', 'height_cm', 'weight_kg') disponibles para el análisis de atletas.")
    else:
        selected_metric = st.selectbox("Selecciona Métrica:", available_numeric_cols, key='athlete_metric')
        # Agrupar por 'gender', 'medal', 'type'
        group_by_options = ['gender', 'medal', 'type', 'Ninguno']
        valid_group_by = [opt for opt in group_by_options if opt == 'Ninguno' or opt in df_filtered.columns]
        group_by_cat = st.selectbox("Agrupar por:", valid_group_by, key='athlete_group')

        st.markdown(f"### Distribución de {selected_metric.replace('_', ' ').title()}")
        # Usar 'gender' para el mapeo de colores
        color_discrete_map = {'Male': 'blue', 'Female': 'red', 'Mixed': 'green'} # Ajusta si tus valores de 'gender' son otros

        # Preparar datos para plot (eliminar NaNs en métrica y grupo si se usa)
        plot_data = df_filtered.copy()
        dropna_subset = [selected_metric]
        if group_by_cat != 'Ninguno' and group_by_cat in plot_data.columns:
            dropna_subset.append(group_by_cat)
        plot_data.dropna(subset=dropna_subset, inplace=True)


        if not plot_data.empty:
            if group_by_cat != 'Ninguno':
                fig_dist = px.violin(plot_data, y=selected_metric, color=group_by_cat,
                                    box=True, points="outliers",
                                    labels={selected_metric: selected_metric.replace('_', ' ').title(), group_by_cat: group_by_cat.title()},
                                    title=f"Distribución de {selected_metric.replace('_', ' ').title()} por {group_by_cat.title()}",
                                    template='plotly_white',
                                    color_discrete_map=color_discrete_map if group_by_cat == 'gender' else None
                                    )
            else:
                fig_dist = px.histogram(plot_data, x=selected_metric, marginal='box',
                                    labels={selected_metric: selected_metric.replace('_', ' ').title()},
                                    title=f"Distribución de {selected_metric.replace('_', ' ').title()}",
                                    template='plotly_white')
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.warning(f"No hay datos válidos para mostrar la distribución de '{selected_metric}' con la agrupación seleccionada.")


        # Scatter Plot Altura vs Peso (usar 'height_cm', 'weight_kg')
        if 'height_cm' in available_numeric_cols and 'weight_kg' in available_numeric_cols:
            st.markdown("### Relación Altura vs. Peso")
            # Colorear por 'gender' o 'medal'
            scatter_color_options = ['gender', 'medal', 'Ninguno']
            valid_scatter_color = [opt for opt in scatter_color_options if opt == 'Ninguno' or opt in df_filtered.columns]
            scatter_color = st.selectbox("Colorear puntos por:", valid_scatter_color, key='scatter_color')
            color_arg = scatter_color if scatter_color != 'Ninguno' else None

            # Preparar datos para scatter (eliminar NaNs en height, weight y color si se usa)
            scatter_dropna_subset = ['height_cm', 'weight_kg']
            if color_arg:
                scatter_dropna_subset.append(color_arg)
            scatter_data = df_filtered.dropna(subset=scatter_dropna_subset).copy()


            if not scatter_data.empty:
                fig_scatter_hw = px.scatter(scatter_data,
                                            x='height_cm', y='weight_kg',
                                            color=color_arg,
                                            title="Relación Altura vs. Peso",
                                            labels={'height_cm': 'Altura (cm)', 'weight_kg': 'Peso (kg)'},
                                            hover_name='name', # Usar 'name' para hover
                                            hover_data=['age', 'noc', 'discipline', 'medal'],
                                            template='plotly_white',
                                            color_discrete_map=color_discrete_map if color_arg == 'gender' else None,
                                            opacity=0.6
                                            )
                st.plotly_chart(fig_scatter_hw, use_container_width=True)
            else:
                st.warning("No hay datos válidos (altura, peso) para mostrar el gráfico de dispersión.")


# --- PESTAÑA 4: ANÁLISIS POR DISCIPLINA ---
with tab_disciplines:
    st.header("Análisis por Disciplinas y Grupos de Disciplinas")

    # Usar 'discipline_grouped' y 'discipline'
    if 'discipline_grouped' in df_filtered.columns and 'discipline' in df_filtered.columns:

        col1, col2 = st.columns([1, 2]) # Columna de filtros más pequeña

        with col1:
            st.markdown("#### Filtros")
            # Seleccionar grupo de disciplina
            # Ordenar opciones alfabéticamente para mejor usabilidad
            discipline_groups = ['Todos'] + sorted(list(df_filtered['discipline_grouped'].unique()))
            selected_group = st.selectbox("Filtrar por Grupo de Disciplina:", discipline_groups, key='disc_group')

            df_disciplines_filtered = df_filtered.copy()
            if selected_group != 'Todos':
                df_disciplines_filtered = df_disciplines_filtered[df_disciplines_filtered['discipline_grouped'] == selected_group]

            # Seleccionar disciplina específica (si se ha filtrado grupo)
            if selected_group != 'Todos':
                # Ordenar opciones alfabéticamente
                specific_disciplines = ['Todas'] + sorted(list(df_disciplines_filtered['discipline'].unique()))
                selected_specific_discipline = st.selectbox(f"Filtrar por Disciplina Específica (en {selected_group}):", specific_disciplines, key='disc_specific')
                if selected_specific_discipline != 'Todas':
                    df_disciplines_filtered = df_disciplines_filtered[df_disciplines_filtered['discipline'] == selected_specific_discipline]


        with col2:
            # Treemap de Participación por Disciplina Agrupada
            st.markdown("#### Distribución de Atletas por Disciplina")
            if not df_disciplines_filtered.empty and 'name' in df_disciplines_filtered.columns:
                # Contar atletas únicos ('name')
                participation_counts = df_disciplines_filtered.groupby(['discipline_grouped', 'discipline'])['name'].nunique().reset_index(name='Athlete Count')

                fig_treemap = px.treemap(participation_counts,
                                    path=[px.Constant("Todas las Disciplinas"), 'discipline_grouped', 'discipline'],
                                    values='Athlete Count',
                                    title='Distribución Jerárquica de Atletas Únicos',
                                    labels={'Athlete Count': 'Número de Atletas Únicos'},
                                    color_discrete_sequence=px.colors.qualitative.Pastel,
                                    template='plotly_white'
                                    )
                fig_treemap.update_traces(textinfo = "label+value+percent parent")
                st.plotly_chart(fig_treemap, use_container_width=True)
            else:
                st.warning("No hay datos para mostrar en el Treemap con los filtros seleccionados o falta la columna 'name'.")

        # Comparación de métricas (ej. Edad) entre disciplinas
        st.markdown("---")
        st.markdown("#### Comparación de Edad Promedio entre Disciplinas")
        # Usar 'age' y 'discipline'
        if 'age' in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered['age']) and 'discipline' in df_filtered.columns:
            # Calcular edad promedio por disciplina (Top N por número de atletas)
            athletes_per_discipline = df_filtered.groupby('discipline')['name'].nunique().reset_index(name='athlete_count')
            top_disciplines_by_athletes = athletes_per_discipline.nlargest(20, 'athlete_count')['discipline'].tolist()

            # Filtrar el df principal para estas disciplinas y calcular edad promedio
            age_by_discipline = df_filtered[df_filtered['discipline'].isin(top_disciplines_by_athletes)].groupby('discipline')['age'].mean().reset_index().sort_values('age', ascending=False)

            fig_age_discipline = px.bar(age_by_discipline, x='discipline', y='age',
                                    title="Edad Promedio por Disciplina (Top 20 por Nº Atletas)",
                                    labels={'discipline': 'Disciplina', 'age': 'Edad Promedio'},
                                    template='plotly_white')
            st.plotly_chart(fig_age_discipline, use_container_width=True)
        else:
            st.warning("Columnas 'age' o 'discipline' no disponibles o no numéricas para comparación entre disciplinas.")

    else:
        st.warning("Columnas 'discipline_grouped' o 'discipline' no encontradas. Análisis por disciplina no disponible.")

# --- Footer Opcional ---
st.markdown("---")
st.caption("Dashboard interactivo creado por Laura Suárez, Laura Sánchez, Alberto Domínguez y Manolo Castillo 😉 con Streamlit y Plotly.")
# st.caption("Fuente de datos: Reboot Academy")