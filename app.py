import app as ap
import pandas as pd
import streamlit as st
import pydeck as pdk
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Análisis Olímpico Interactivo", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv("jjoo.csv", parse_dates=['born_date'])
    return df

df = load_data()

# Separar por tipo de Juegos
df_summer = df[df['type'] == 'Summer']
df_winter = df[df['type'] == 'Winter']

# Sidebar: Filtros interactivos
st.sidebar.header("Filtros")
tipo_juego = st.sidebar.radio("Tipo de Juegos", ["Verano", "Invierno"])
df_tipo = df_summer if tipo_juego == 'Verano' else df_winter

# Filtro de país
paises = df_tipo['noc'].unique()
paises.sort()
pais = st.sidebar.selectbox("País (NOC)", options=['Todos'] + list(paises))
if pais != 'Todos':
    df_tipo = df_tipo[df_tipo['noc'] == pais]

# Filtro de medalla
medalla = st.sidebar.selectbox("Tipo de medalla", options=['Todas', 'Gold', 'Silver', 'Bronze'])
if medalla != 'Todas':
    df_tipo = df_tipo[df_tipo['medal'] == medalla]

# Filtro de género
genero = st.sidebar.selectbox("Género", options=['Ambos', 'M', 'F'])
if genero != 'Ambos':
    df_tipo = df_tipo[df_tipo['gender'] == genero]

# ============ VISUALIZACIONES ============

st.title(f"Juegos Olímpicos de {tipo_juego} - Dashboard Interactivo")

# --- Gráfico 1: Evolución histórica por género ---
st.subheader("📊 Evolución histórica por género")
fig1, ax1 = plt.subplots(figsize=(12, 5))
sns.countplot(data=df_tipo, x='year', hue='gender', palette='Set2', ax=ax1)
plt.xticks(rotation=45)
st.pyplot(fig1)

# --- Gráfico 2: Edad por disciplina (boxplot) ---
st.subheader("📦 Boxplot: Edad por disciplina")
fig2, ax2 = plt.subplots(figsize=(12, 6))
sns.boxplot(data=df_tipo, x='discipline_grouped', y='age', hue='gender', palette='coolwarm', ax=ax2)
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
st.pyplot(fig2)

# --- Gráfico 3: Conteo de medallas por país ---
st.subheader("🥇 Conteo de Medallas por País")
medallas_pais = df_tipo[df_tipo['medal'].isin(['Gold', 'Silver', 'Bronze'])].groupby('noc')['medal'].count().sort_values(ascending=False).head(15)
fig3, ax3 = plt.subplots(figsize=(10, 5))
medallas_pais.plot(kind='bar', color='gold', ax=ax3)
ax3.set_ylabel("Cantidad de Medallas")
st.pyplot(fig3)

# --- Gráfico 4: Mapa (opcional) ---
# st.subheader("🌍 Mapa interactivo por país (requiere coordenadas)")
# if 'geolocalizacion_completa.csv' in df.columns:
#     df_coords = df[['noc', 'noc_coords']].drop_duplicates()
#     df_coords[['Latitude', 'lon']] = df_coords['noc_coords'].str.split(',', expand=True).astype(float)
#     df_mapa = df_coords.merge(medallas_pais.reset_index(), on='noc')
#     st.map(df_mapa.rename(columns={'Latitude': 'latitude', 'lon': 'longitude'}))

# # --- Tabla opcional ---
# if st.checkbox("Mostrar tabla de datos filtrados"):
#     st.dataframe(df_tipo[['year', 'name', 'noc', 'gender', 'discipline_grouped', 'age', 'medal']].reset_index(drop=True).head(100))


# # Code,Country,Capital,Latitude,Longitude


st.set_page_config(page_title="Mapa Olímpico Interactivo", layout="wide")

st.title("🌍 Mapa Interactivo de Participación Olímpica")
st.markdown("Visualiza países y capitales junto con sus datos olímpicos (medallas, participantes, etc.).")

@st.cache_data
def load_data():
    geo = pd.read_csv("geolocalizacion_completa.csv")
    jjoo = pd.read_csv("jjoo.csv")
    df_join = jjoo.merge(geo, left_on="noc", right_on="noc", how="left")
    return df_join

df_join = load_data()

# Filtro por tipo de medalla
medalla_seleccionada = st.selectbox("Filtrar por medalla", ["Todas", "Gold", "Silver", "Bronze"])
if medalla_seleccionada != "Todas":
    df_join = df_join[df_join['medal'].str.lower() == medalla_seleccionada.lower()]

# Mostrar tabla si se desea
if st.checkbox("Mostrar tabla de datos combinados"):
    st.dataframe(df_join)

# Mapa interactivo
st.subheader("🗺️ Mapa de países participantes")
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=1,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=df_join.dropna(subset=['latitude', 'longitude']),
            get_position='[longitude, latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=300000,
            pickable=True
        )
    ],
    tooltip={"text": "{País}\n{Capital}\nMedalla: {medal}"}
))
