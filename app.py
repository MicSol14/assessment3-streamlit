import streamlit as st
import pandas as pd
import plotly.express as px

# Konfiguracja strony głównej
st.set_page_config(page_title="Sustainable Energy Dashboard", layout="wide")

# ==========================================
# 1. WCZYTYWANIE I CZYSZCZENIE DANYCH
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv('global-data-on-sustainable-energy.csv')
    
    # Zmiana nazw kolumn na krótsze dla wygody
    df.rename(columns={
        'Access to electricity (% of population)': 'Electricity Access (%)',
        'Value_co2_emissions_kt_by_country': 'CO2 Emissions (kt)',
        'Renewable energy share in the total final energy consumption (%)': 'Renewable Share (%)',
        'gdp_per_capita': 'GDP per Capita',
        'Electricity from fossil fuels (TWh)': 'Fossil Fuels (TWh)',
        'Electricity from renewables (TWh)': 'Renewables (TWh)',
        'Electricity from nuclear (TWh)': 'Nuclear (TWh)'
    }, inplace=True)
    
    # FILTRACJA: Usunięcie roku 2020 z powodu niekompletnych danych w bazie
    df = df[df['Year'] < 2020]
    
    # Wypełnianie brakujących danych numerycznych medianą lub zerem (bezpieczne dla trendów)
    cols_to_fill = ['CO2 Emissions (kt)', 'Renewable Share (%)', 'GDP per Capita',
                    'Fossil Fuels (TWh)', 'Renewables (TWh)', 'Nuclear (TWh)', 'Electricity Access (%)']
    for col in cols_to_fill:
        df[col] = df[col].fillna(0)
        
    return df

df = load_data()

# ==========================================
# 2. PANEL BOCZNY (INTERAKTYWNE FILTRY)
# ==========================================
st.sidebar.header("Opcje filtrowania")

# Slider zakresu lat
min_year = int(df['Year'].min())
max_year = int(df['Year'].max())
selected_years = st.sidebar.slider("Wybierz zakres lat", min_year, max_year, (2000, max_year))

# Multiselect dla krajów - TERAZ DOMYŚLNIE POLSKA I NORWEGIA
all_countries = sorted(df['Entity'].unique())
selected_countries = st.sidebar.multiselect(
    "Wybierz kraje do porównania trendów", 
    all_countries, 
    default=["Norway", "Poland"]
)

# Aplikowanie filtrów
filtered_df = df[(df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1])]
country_df = filtered_df[filtered_df['Entity'].isin(selected_countries)]

# ==========================================
# 3. GŁÓWNY DASHBOARD
# ==========================================
st.title("🌍 Global Sustainable Energy Analysis (2000-2019)")
st.markdown("Interaktywny panel analizujący wskaźniki energii odnawialnej, emisji CO2 i dostępu do prądu na świecie.")

# Wizualizacja 1: Mapa Świata (Choropleth) - Zależna od wybranego roku
st.subheader(f"Dostęp do elektryczności na świecie w roku {selected_years[1]}")
map_df = df[df['Year'] == selected_years[1]]

fig_map = px.choropleth(
    map_df, 
    locations="Entity", 
    locationmode='country names',
    color="Electricity Access (%)", 
    hover_name="Entity",
    color_continuous_scale="YlGnBu",  # Sprawdzona sekwencyjna skala kolorów
    range_color=[0, 100],               
    title=f"Access to Electricity (%) in {selected_years[1]}"
)
fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")
st.subheader("Porównanie wybranych krajów")

if not selected_countries:
    st.warning("Wybierz co najmniej jeden kraj z panelu bocznego, aby zobaczyć szczegóły.")
else:
    # KPI Metrics
    col1, col2, col3 = st.columns(3)
    latest_data = country_df[country_df['Year'] == selected_years[1]]
    
    with col1:
        avg_co2 = latest_data['CO2 Emissions (kt)'].mean()
        st.metric(label=f"Średnia Emisja CO2 w {selected_years[1]} (kt)", value=f"{avg_co2:,.0f}")
    with col2:
        avg_ren = latest_data['Renewable Share (%)'].mean()
        st.metric(label=f"Średni udział OZE w {selected_years[1]}", value=f"{avg_ren:.1f}%")
    with col3:
        avg_gdp = latest_data['GDP per Capita'].mean()
        st.metric(label=f"Średnie PKB per Capita w {selected_years[1]}", value=f"${avg_gdp:,.0f}")

    # Wizualizacja 2: Emisja CO2 (Line Chart)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_line = px.line(
            country_df, x="Year", y="CO2 Emissions (kt)", color="Entity",
            title="Trendy emisji CO2", markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # Wizualizacja 3: Udział Energii Odnawialnej (Bar Chart)
    with col_chart2:
        fig_bar = px.bar(
            country_df, x="Year", y="Renewable Share (%)", color="Entity", barmode="group",
            title="Udział energii odnawialnej w konsumpcji (%)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Wizualizacja 4: Mix energetyczny - Paliwa kopalne vs OZE (Area Chart)
    st.subheader("Porównanie Miksu Energetycznego (TWh)")
    mix_df = country_df.melt(id_vars=['Entity', 'Year'], 
                             value_vars=['Fossil Fuels (TWh)', 'Renewables (TWh)', 'Nuclear (TWh)'],
                             var_name='Energy Source', value_name='TWh')
    
    fig_area = px.area(
        mix_df, x="Year", y="TWh", color="Energy Source", facet_col="Entity",
        title="Źródła produkcji energii elektrycznej w czasie"
    )
    st.plotly_chart(fig_area, use_container_width=True)

    # Wizualizacja 5: Zależność PKB od udziału OZE (Scatter Plot - Bubble)
    st.subheader("Zależność między bogactwem a energią odnawialną")
    fig_scatter = px.scatter(
        country_df, x="GDP per Capita", y="Renewable Share (%)", size="CO2 Emissions (kt)", 
        color="Entity", hover_name="Entity", animation_frame="Year",
        title="PKB per capita vs. Udział OZE (Wielkość = Emisja CO2)",
        size_max=50, range_x=[0, country_df['GDP per Capita'].max() + 5000],
        range_y=[0, 100]
    )
    st.plotly_chart(fig_scatter, use_container_width=True)