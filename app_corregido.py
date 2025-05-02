
import pandas as pd
import streamlit as st
import pydeck as pdk
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# ✅ SOLO UNA VEZ y justo al principio
st.set_page_config(page_title="Análisis Olímpico Interactivo", layout="wide")

# ========= CARGA DE DATOS =========
@st.cache_data
def load_main_data():
    df = pd.read_csv("jjoo.csv", parse_dates=['born_date'])
    return df

@st.cache_data
def load_geodata():
    geo = pd.read_csv("geolocalizacion_completa.csv")
    return geo

df = load_main_data()
geo_df = load_geodata()
df_join = df.merge(geo_df, left_on="noc", right_on="noc", how="left")

# ========= SIDEBAR CON FILTROS =========
st.sidebar.header("🎛️ Filtros")

tipo_juego = st.sidebar.radio("Tipo de Juegos", ["Verano", "Invierno"])
df_tipo = df[df['type'] == ('Summer' if tipo_juego == 'Verano' else 'Winter')]

paises = df_tipo['noc'].dropna().unique()
paises.sort()
pais = st.sidebar.selectbox("País (noc)", options=['Todos'] + list(paises))
if pais != 'Todos':
    df_tipo = df_tipo[df_tipo['noc'] == pais]

medalla = st.sidebar.selectbox("Tipo de medalla", options=['Todas', 'Gold', 'Silver', 'Bronze'])
if medalla != 'Todas':
    df_tipo = df_tipo[df_tipo['medal'] == medalla]

genero = st.sidebar.selectbox("Género", options=['Ambos', 'M', 'F'])
if genero != 'Ambos':
    df_tipo = df_tipo[df_tipo['gender'] == genero]

# ========= VISUALIZACIONES =========
st.title(f"Juegos Olímpicos de {tipo_juego} - Dashboard Interactivo")

# --- Gráfico 1: Evolución histórica por género ---
st.subheader("📊 Evolución histórica por género")
fig1, ax1 = plt.subplots(figsize=(12, 5))
sns.countplot(data=df_tipo, x='year', hue='gender', palette='Set2', ax=ax1)
plt.xticks(rotation=45)
st.pyplot(fig1)

# --- Gráfico 2: Edad por disciplina (boxplot) ---
st.subheader("📦 Boxplot: Edad por disciplina")
if 'discipline_grouped' in df_tipo.columns:
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=df_tipo, x='discipline_grouped', y='age', hue='gender', palette='coolwarm', ax=ax2)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
    st.pyplot(fig2)

# --- Gráfico 3: Conteo de Medallas por País ---
st.subheader("🥇 Conteo de Medallas por País")
medallas_pais = df_tipo[df_tipo['medal'].isin(['Gold', 'Silver', 'Bronze'])].groupby('noc')['medal'].count().sort_values(ascending=False).head(15)
fig3, ax3 = plt.subplots(figsize=(10, 5))
medallas_pais.plot(kind='bar', color='gold', ax=ax3)
ax3.set_ylabel("Cantidad de Medallas")
st.pyplot(fig3)

# ========= MAPA INTERACTIVO =========
st.subheader("🗺️ Mapa de países participantes")
medalla_seleccionada = st.selectbox("Filtrar por medalla en el mapa", ["Todas", "Gold", "Silver", "Bronze"])
df_mapa = df_join.copy()
if medalla_seleccionada != "Todas":
    df_mapa = df_mapa[df_mapa['medal'].str.lower() == medalla_seleccionada.lower()]

if st.checkbox("Mostrar tabla de datos combinados"):
    st.dataframe(df_mapa)

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
            data=df_mapa.dropna(subset=['latitude', 'longitude']),
            get_position='[longitude, latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=300000,
            pickable=True
        )
    ],
    tooltip={"text": "{País}\n{Capital}\nMedalla: {medal}"}
))
