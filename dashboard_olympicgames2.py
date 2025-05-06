import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="Historical Olympic Games Analysis",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading Functions ---

@st.cache_data  # Caches the result to improve performance
def load_data(filepath='jjoo.csv'):
    """Loads the preprocessed CSV file 'jjoo.csv'."""
    try:
        df = pd.read_csv(filepath)
        # Optional: Convert columns if not loaded with the correct type
        # df['born_date'] = pd.to_datetime(df['born_date'], errors='coerce')
        # df['year'] = pd.to_numeric(df['year'], errors='coerce')
        # ... etc ...

        # Verify essential columns (adjust as needed)
        essential_cols = ['year', 'type', 'noc', 'medal', 'age', 'gender', 'discipline_grouped', 'name', 'discipline']
        missing_cols = [col for col in essential_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing essential columns in '{filepath}': {', '.join(missing_cols)}")
            return pd.DataFrame()

        st.success(f"File '{filepath}' loaded successfully ({len(df):,} rows).")
        return df
    except FileNotFoundError:
        st.error(f"Error: File '{filepath}' not found. Make sure it's in the same directory as the script.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading or processing '{filepath}': {e}")
        return pd.DataFrame()


@st.cache_data
def load_noc_coords(filepath='noc_coordinates.csv'):
    """Loads NOC coordinates and country name data."""
    try:
        df_coords = pd.read_csv(filepath)
        # Verify required columns
        if 'noc' not in df_coords.columns or 'country' not in df_coords.columns or \
           'latitude' not in df_coords.columns or 'longitude' not in df_coords.columns:
            st.error(f"The file '{filepath}' must contain the columns 'noc', 'country', 'latitude', 'longitude'.")
            return pd.DataFrame(columns=['noc', 'country', 'latitude', 'longitude'])
        
        # Ensure no NaNs in key columns
        df_coords.dropna(subset=['noc', 'country', 'latitude', 'longitude'], inplace=True)
        return df_coords[['noc', 'country', 'latitude', 'longitude']]
    except FileNotFoundError:
        st.error(f"File '{filepath}' not found. Make sure it is in the correct path.")
        return pd.DataFrame(columns=['noc', 'country', 'latitude', 'longitude'])
    except Exception as e:
        st.error(f"Error loading or processing '{filepath}': {e}")
        return pd.DataFrame(columns=['noc', 'country', 'latitude', 'longitude'])

# --- Load Data ---
df_olympics = load_data()
df_coords = load_noc_coords()

# --- Sidebar for Global Filters ---
st.sidebar.header("Global Filters 🌍")

if df_olympics.empty:
    st.sidebar.error("Main data file ('jjoo.csv') could not be loaded. The app cannot proceed.")
    st.stop()  # Stop execution if no data is loaded

# --- Filters ---
# Ensure 'year' is numeric before using min/max
if pd.api.types.is_numeric_dtype(df_olympics['year']):
    min_year = int(df_olympics['year'].min())
    max_year = int(df_olympics['year'].max())
    selected_years = st.sidebar.slider(
        "Select Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)  # Default to full range
    )
else:
    st.sidebar.error("The 'year' column is not numeric or was not loaded properly.")
    selected_years = (0, 0)  # Invalid placeholder value

# Filter by game type ('type' column)
if 'type' in df_olympics.columns:
    type_options = ['All'] + list(df_olympics['type'].unique())
    selected_type = st.sidebar.radio(
        "Game Type",
        options=type_options,
        index=0  # Default to 'All'
    )
else:
    st.sidebar.warning("'type' column not found. Cannot filter by game type.")
    selected_type = 'All'

# Filter by gender ('gender' column)
if 'gender' in df_olympics.columns:
    gender_options = list(df_olympics['gender'].unique())
    # Remove NaNs if present in options
    gender_options = [g for g in gender_options if pd.notna(g)]
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        options=gender_options,
        default=gender_options  # Default to all selected
    )
else:
    st.sidebar.warning("'gender' column not found. Cannot filter by gender.")
    selected_gender = []

# --- Filter the Main DataFrame ---
df_filtered = df_olympics[
    (df_olympics['year'] >= selected_years[0]) &
    (df_olympics['year'] <= selected_years[1])
]
if selected_type != 'All' and 'type' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['type'] == selected_type]

if selected_gender and 'gender' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['gender'].isin(selected_gender)]

# --- Check if any data remains after filtering ---
if df_filtered.empty and not df_olympics.empty:
    st.warning("No data available for the selected filters. Please adjust the filters.")
    st.stop()  # Stop if there's no data to display

# --- Main Title ---
st.title("🏅 Interactive Analysis of Historical Olympic Games 🏅")
st.markdown(f"Displaying data from **{selected_years[0]}** to **{selected_years[1]}**.")
# Display selected game type if not 'All'
if selected_type != 'All':
    st.markdown(f"Game Type: **{selected_type}**")
st.markdown("---")

# --- Tabs for organizing content ---
tab_overview, tab_geo, tab_athletes, tab_disciplines = st.tabs([
    "📈 Overview",
    "🌍 Geographic Analysis",
    "🧍 Athlete Analysis",
    "🤸 Discipline Analysis"
])

# --- TAB 1: OVERVIEW ---
with tab_overview:
    st.header("General Participation Trends")

    col1, col2 = st.columns(2)
    with col1:
        # Use 'name' for unique athletes
        total_athletes = df_filtered['name'].nunique()
        st.metric("Unique Athletes", f"{total_athletes:,}")
    with col2:
        # Use 'noc' for unique countries
        total_countries = df_filtered['noc'].nunique()
        st.metric("Participating Countries (NOCs)", f"{total_countries:,}")

    st.markdown("### Participation Over Time by Gender")
    if 'year' in df_filtered.columns and 'gender' in df_filtered.columns:
        participation_over_time = df_filtered.groupby(['year', 'gender']).size().reset_index(name='Count')
        fig_participation = px.area(participation_over_time, x='year', y='Count', color='gender',
                                    labels={'year': 'Year', 'Count': 'Number of Participants', 'gender': 'Gender'},
                                    markers=True, template='plotly_white')
        fig_participation.update_layout(hovermode="x unified")
        st.plotly_chart(fig_participation, use_container_width=True)
    else:
        st.warning("'year' or 'gender' columns not available for the trend chart.")

    st.markdown("### Number of Disciplines per Year")
    if 'year' in df_filtered.columns and 'discipline' in df_filtered.columns:
        # Use 'discipline' to count unique disciplines
        disciplines_over_time = df_filtered.groupby('year')['discipline'].nunique().reset_index()
        fig_disciplines = px.line(disciplines_over_time, x='year', y='discipline',
                                title="Number of Olympic Disciplines Over Time",
                                labels={'year': 'Year', 'discipline': 'Number of Unique Disciplines'},
                                markers=True, template='plotly_white')
        st.plotly_chart(fig_disciplines, use_container_width=True)
    else:
        st.warning("'year' or 'discipline' columns not available for discipline chart.")

# --- TAB 2: GEOGRAPHIC ANALYSIS ---
with tab_geo:
    st.header("Performance and Participation by Country (NOC)")

    # Calculate metrics per NOC (using 'noc', 'name', 'medal')
    # Ensure 'medal' doesn't contain only NaNs or unexpected values
    df_filtered['medal_present'] = df_filtered['medal'].notna() & (df_filtered['medal'] != 'No Medal')  # Adjust if using a different placeholder

    metrics_by_noc = df_filtered.groupby('noc').agg(
        Total_Athletes=('name', 'nunique'),
        Total_Medals=('medal_present', 'sum'),  # Sum of True (1) where medals exist
        # Count specific medals (ensure strings match your dataset)
        Gold=('medal', lambda x: (x == 'Gold').sum()),
        Silver=('medal', lambda x: (x == 'Silver').sum()),
        Bronze=('medal', lambda x: (x == 'Bronze').sum())
    ).reset_index()
    # Convert Total_Medals to int
    metrics_by_noc['Total_Medals'] = metrics_by_noc['Total_Medals'].astype(int)
    # Add option to sort countries
    sort_options = ['Total_Medals', 'Total_Athletes', 'Gold', 'Silver', 'Bronze']
    valid_sort_options = [opt for opt in sort_options if opt in metrics_by_noc.columns]  # Only valid options
    if not valid_sort_options:
        st.warning("Metrics could not be calculated to sort countries.")
    else:
        sort_by = st.selectbox("Sort countries by:", valid_sort_options, key='geo_sort')
        top_n = st.slider("Show Top N Countries:", min_value=5, max_value=50, value=15, key='geo_topn')

        top_countries = metrics_by_noc.sort_values(by=sort_by, ascending=False).head(top_n)

        # Bar Chart for Top Countries
        st.markdown(f"### Top {top_n} Countries by {sort_by.replace('_', ' ')}")
        fig_top_countries = px.bar(top_countries, x='noc', y=sort_by,
                                   hover_data=['Total_Athletes', 'Gold', 'Silver', 'Bronze'],
                                   labels={'noc': 'Country (NOC)', sort_by: sort_by.replace('_', ' ')},
                                   template='plotly_white',
                                   color=sort_by,
                                   color_continuous_scale=px.colors.sequential.Plasma)
        st.plotly_chart(fig_top_countries, use_container_width=True)

    # Scatter Mapbox Chart
    st.markdown("### Geographic Distribution of Medals")
    if not df_coords.empty and 'noc' in metrics_by_noc.columns:
        # Merge metrics with coordinates using 'noc'
        df_map_data = pd.merge(metrics_by_noc[metrics_by_noc['Total_Medals'] > 0], df_coords, on='noc', how='left')
        df_map_data.dropna(subset=['latitude', 'longitude'], inplace=True)

        if not df_map_data.empty:
            fig_scatter_map = px.scatter_mapbox(
                df_map_data,
                lat="latitude",
                lon="longitude",
                size="Total_Medals",
                color="Total_Medals",
                hover_name="country",  # Use 'country' for primary display
                hover_data={
                    "latitude": False, "longitude": False,
                    "noc": True, "country": False, "Total_Medals": True, "Total_Athletes": True,
                    "Gold": True, "Silver": True, "Bronze": True
                },
                color_continuous_scale=px.colors.sequential.Viridis,
                size_max=60,
                zoom=0.8,
                mapbox_style="carto-positron",
                title="Geographic Distribution of Total Medals by NOC"
            )
            fig_scatter_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
            st.plotly_chart(fig_scatter_map, use_container_width=True)
        else:
            st.warning("Could not merge medal data with coordinates for the map.")
    else:
        st.warning("Coordinate data ('noc_coordinates.csv') not loaded or 'noc' column not found for map creation.")
# --- TAB 3: ATHLETE ANALYSIS ---
with tab_athletes:
    st.header("Physical and Demographic Characteristics of Athletes")

    # Use column names from olympics.csv: 'age', 'height_cm', 'weight_kg'
    numeric_cols = ['age', 'height_cm', 'weight_kg']
    available_numeric_cols = [
        col for col in numeric_cols if col in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered[col])
    ]

    if not available_numeric_cols:
        st.warning("No numeric columns ('age', 'height_cm', 'weight_kg') available for athlete analysis.")
    else:
        selected_metric = st.selectbox("Select Metric:", available_numeric_cols, key='athlete_metric')
        # Group by 'gender', 'medal', 'type'
        group_by_options = ['gender', 'medal', 'type', 'None']
        valid_group_by = [opt for opt in group_by_options if opt == 'None' or opt in df_filtered.columns]
        group_by_cat = st.selectbox("Group by:", valid_group_by, key='athlete_group')

        st.markdown(f"### Distribution of {selected_metric.replace('_', ' ').title()}")
        # Use 'gender' for color mapping
        color_discrete_map = {'Male': 'blue', 'Female': 'red', 'Mixed': 'green'}  # Adjust if your 'gender' values differ

        # Prepare data for plotting (remove NaNs in metric and group if used)
        plot_data = df_filtered.copy()
        dropna_subset = [selected_metric]
        if group_by_cat != 'None' and group_by_cat in plot_data.columns:
            dropna_subset.append(group_by_cat)
        plot_data.dropna(subset=dropna_subset, inplace=True)

        if not plot_data.empty:
            if group_by_cat != 'None':
                fig_dist = px.violin(
                    plot_data, y=selected_metric, color=group_by_cat,
                    box=True, points="outliers",
                    labels={
                        selected_metric: selected_metric.replace('_', ' ').title(),
                        group_by_cat: group_by_cat.title()
                    },
                    title=f"Distribution of {selected_metric.replace('_', ' ').title()} by {group_by_cat.title()}",
                    template='plotly_white',
                    color_discrete_map=color_discrete_map if group_by_cat == 'gender' else None
                )
            else:
                fig_dist = px.histogram(
                    plot_data, x=selected_metric, marginal='box',
                    labels={selected_metric: selected_metric.replace('_', ' ').title()},
                    title=f"Distribution of {selected_metric.replace('_', ' ').title()}",
                    template='plotly_white'
                )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.warning(f"No valid data available to show the distribution of '{selected_metric}' with the selected grouping.")
        # Scatter Plot: Height vs Weight
        if 'height_cm' in available_numeric_cols and 'weight_kg' in available_numeric_cols:
            st.markdown("### Height vs Weight Relationship")
            # Color by 'gender' or 'medal'
            scatter_color_options = ['gender', 'medal', 'None']
            valid_scatter_color = [opt for opt in scatter_color_options if opt == 'None' or opt in df_filtered.columns]
            scatter_color = st.selectbox("Color points by:", valid_scatter_color, key='scatter_color')
            color_arg = scatter_color if scatter_color != 'None' else None

            # Prepare data for scatter plot (remove NaNs in height, weight, and color if used)
            scatter_dropna_subset = ['height_cm', 'weight_kg']
            if color_arg:
                scatter_dropna_subset.append(color_arg)
            scatter_data = df_filtered.dropna(subset=scatter_dropna_subset).copy()

            if not scatter_data.empty:
                fig_scatter_hw = px.scatter(
                    scatter_data,
                    x='height_cm', y='weight_kg',
                    color=color_arg,
                    title="Height vs Weight Relationship",
                    labels={'height_cm': 'Height (cm)', 'weight_kg': 'Weight (kg)'},
                    hover_name='name',  # Use 'name' for hover
                    hover_data=['age', 'noc', 'discipline', 'medal'],
                    template='plotly_white',
                    color_discrete_map=color_discrete_map if color_arg == 'gender' else None,
                    opacity=0.6
                )
                st.plotly_chart(fig_scatter_hw, use_container_width=True)
            else:
                st.warning("No valid data (height, weight) available to display the scatter plot.")

# --- TAB 4: DISCIPLINE ANALYSIS ---
with tab_disciplines:
    st.header("Analysis by Disciplines and Discipline Groups")

    # Use 'discipline_grouped' and 'discipline'
    if 'discipline_grouped' in df_filtered.columns and 'discipline' in df_filtered.columns:

        col1, col2 = st.columns([1, 2])  # Smaller filter column

        with col1:
            st.markdown("#### Filters")
            # Select discipline group
            # Sort options alphabetically for better usability
            discipline_groups = ['All'] + sorted(list(df_filtered['discipline_grouped'].unique()))
            selected_group = st.selectbox("Filter by Discipline Group:", discipline_groups, key='disc_group')

            df_disciplines_filtered = df_filtered.copy()
            if selected_group != 'All':
                df_disciplines_filtered = df_disciplines_filtered[
                    df_disciplines_filtered['discipline_grouped'] == selected_group
                ]

            # Select specific discipline (if group was filtered)
            if selected_group != 'All':
                specific_disciplines = ['All'] + sorted(list(df_disciplines_filtered['discipline'].unique()))
                selected_specific_discipline = st.selectbox(
                    f"Filter by Specific Discipline (in {selected_group}):",
                    specific_disciplines,
                    key='disc_specific'
                )
                if selected_specific_discipline != 'All':
                    df_disciplines_filtered = df_disciplines_filtered[
                        df_disciplines_filtered['discipline'] == selected_specific_discipline
                    ]

        with col2:
            # Treemap of Participation by Discipline Group
            st.markdown("#### Athlete Distribution by Discipline")
            if not df_disciplines_filtered.empty and 'name' in df_disciplines_filtered.columns:
                # Count unique athletes ('name')
                participation_counts = df_disciplines_filtered.groupby(
                    ['discipline_grouped', 'discipline']
                )['name'].nunique().reset_index(name='Athlete Count')

                fig_treemap = px.treemap(
                    participation_counts,
                    path=[px.Constant("All Disciplines"), 'discipline_grouped', 'discipline'],
                    values='Athlete Count',
                    title='Hierarchical Distribution of Unique Athletes',
                    labels={'Athlete Count': 'Number of Unique Athletes'},
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    template='plotly_white'
                )
                fig_treemap.update_traces(textinfo="percent parent, label+value+percent root")
                st.plotly_chart(fig_treemap, use_container_width=True)
            else:
                st.warning("No data available for the Treemap with the selected filters or the 'name' column is missing.")

        # Metric comparison (e.g., Age) between disciplines
        st.markdown("---")
        st.markdown("#### Average Age Comparison Between Disciplines")
        # Use 'age' and 'discipline'
        if 'age' in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered['age']) and 'discipline' in df_filtered.columns:
            # Calculate average age per discipline (Top N by number of athletes)
            athletes_per_discipline = df_filtered.groupby('discipline')['name'].nunique().reset_index(name='athlete_count')
            top_disciplines_by_athletes = athletes_per_discipline.nlargest(20, 'athlete_count')['discipline'].tolist()

            # Filter main DataFrame for these disciplines and calculate average age
            age_by_discipline = df_filtered[
                df_filtered['discipline'].isin(top_disciplines_by_athletes)
            ].groupby('discipline')['age'].mean().reset_index().sort_values('age', ascending=False)

            fig_age_discipline = px.bar(
                age_by_discipline, x='discipline', y='age',
                title="Average Age by Discipline (Top 20 by Number of Athletes)",
                labels={'discipline': 'Discipline', 'age': 'Average Age'},
                template='plotly_white'
            )
            st.plotly_chart(fig_age_discipline, use_container_width=True)
        else:
            st.warning("'age' or 'discipline' columns not available or not numeric for comparison across disciplines.")
    else:
        st.warning("'discipline_grouped' or 'discipline' columns not found. Discipline analysis not available.")

# --- Optional Footer ---
st.markdown("---")
st.caption("Interactive dashboard created by Laura Suárez, Laura Sánchez, Alberto Domínguez and Manolo Castillo 😉 using Streamlit and Plotly.")
# st.caption("Data source: Reboot Academy")

