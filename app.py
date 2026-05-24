import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sustainable Energy Dashboard", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("global-data-on-sustainable-energy.csv")

    df.rename(
        columns={
            "Access to electricity (% of population)": "Electricity Access (%)",
            "Value_co2_emissions_kt_by_country": "CO2 Emissions (kt)",
            "Renewable energy share in the total final energy consumption (%)": "Renewable Share (%)",
            "gdp_per_capita": "GDP per Capita",
            "Electricity from fossil fuels (TWh)": "Fossil Fuels (TWh)",
            "Electricity from renewables (TWh)": "Renewables (TWh)",
            "Electricity from nuclear (TWh)": "Nuclear (TWh)",
        },
        inplace=True,
    )

    df = df[df["Year"] < 2020]

    cols_to_fill = [
        "CO2 Emissions (kt)",
        "Renewable Share (%)",
        "GDP per Capita",
        "Fossil Fuels (TWh)",
        "Renewables (TWh)",
        "Nuclear (TWh)",
        "Electricity Access (%)",
    ]

    for col in cols_to_fill:
        df[col] = df[col].fillna(0)

    return df


df = load_data()

st.sidebar.header("Filter Options")

min_year = int(df["Year"].min())
max_year = int(df["Year"].max())

selected_years = st.sidebar.slider(
    "Select Year Range",
    min_year,
    max_year,
    (2000, max_year),
)

all_countries = sorted(df["Entity"].unique())

selected_countries = st.sidebar.multiselect(
    "Select Countries for Trend Comparison",
    all_countries,
    default=["Norway", "Poland"],
)

filtered_df = df[(df["Year"] >= selected_years[0]) & (df["Year"] <= selected_years[1])]
country_df = filtered_df[filtered_df["Entity"].isin(selected_countries)]

st.title("🌍 Global Sustainable Energy Analysis (2000–2019)")
st.markdown(
    "Interactive dashboard analysing renewable energy indicators, CO2 emissions, "
    "and global access to electricity."
)

st.subheader(f"Global Electricity Access in {selected_years[1]}")

map_df = df[df["Year"] == selected_years[1]]

fig_map = px.choropleth(
    map_df,
    locations="Entity",
    locationmode="country names",
    color="Electricity Access (%)",
    hover_name="Entity",
    color_continuous_scale="YlGnBu",
    range_color=[0, 100],
    title=f"Access to Electricity (%) in {selected_years[1]}",
)

fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")
st.subheader("Comparison of Selected Countries")

if not selected_countries:
    st.warning("Select at least one country from the sidebar to display detailed analysis.")
else:
    col1, col2, col3 = st.columns(3)
    latest_data = country_df[country_df["Year"] == selected_years[1]]

    with col1:
        avg_co2 = latest_data["CO2 Emissions (kt)"].mean()
        st.metric(
            label=f"Average CO2 Emissions in {selected_years[1]} (kt)",
            value=f"{avg_co2:,.0f}",
        )

    with col2:
        avg_ren = latest_data["Renewable Share (%)"].mean()
        st.metric(
            label=f"Average Renewable Energy Share in {selected_years[1]}",
            value=f"{avg_ren:.1f}%",
        )

    with col3:
        avg_gdp = latest_data["GDP per Capita"].mean()
        st.metric(
            label=f"Average GDP per Capita in {selected_years[1]}",
            value=f"${avg_gdp:,.0f}",
        )

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_line = px.line(
            country_df,
            x="Year",
            y="CO2 Emissions (kt)",
            color="Entity",
            title="CO2 Emissions Trends",
            markers=True,
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_chart2:
        fig_bar = px.bar(
            country_df,
            x="Year",
            y="Renewable Share (%)",
            color="Entity",
            barmode="group",
            title="Renewable Energy Share in Consumption (%)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Energy Mix Comparison (TWh)")

    mix_df = country_df.melt(
        id_vars=["Entity", "Year"],
        value_vars=[
            "Fossil Fuels (TWh)",
            "Renewables (TWh)",
            "Nuclear (TWh)",
        ],
        var_name="Energy Source",
        value_name="TWh",
    )

    fig_area = px.area(
        mix_df,
        x="Year",
        y="TWh",
        color="Energy Source",
        facet_col="Entity",
        title="Electricity Production Sources Over Time",
    )
    st.plotly_chart(fig_area, use_container_width=True)

    st.subheader("Relationship Between Wealth and Renewable Energy")

    fig_scatter = px.scatter(
        country_df,
        x="GDP per Capita",
        y="Renewable Share (%)",
        size="CO2 Emissions (kt)",
        color="Entity",
        hover_name="Entity",
        animation_frame="Year",
        title="GDP per Capita vs Renewable Energy Share (Bubble Size = CO2 Emissions)",
        size_max=50,
        range_x=[0, country_df["GDP per Capita"].max() + 5000],
        range_y=[0, 100],
    )

    st.plotly_chart(fig_scatter, use_container_width=True)
