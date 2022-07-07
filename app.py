import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

# Setting page config to wide mode and adding a title and favicon
st.set_page_config(layout="wide", page_title="Paragliding takeoff and landing sites", page_icon=":hatching_chick:")

# Load data once
# @st.experimental_singleton
def load_data():
    data = pd.read_csv(
        "data_all.csv.gz",
        # nrows=100000,  # approx. 10% of data
        names=[
            # "date/time",
            "lon0",
            "lat0",
            "lon1",
            "lat1",
            "duration",
        ],  # specify names directly since they don't change
        skiprows=1,  # don't read header since names specified directly
        usecols=[1, 2, 4, 5, 6],
    )
    # st.write('Pre-fitering:', data.describe())
    # Filter out far away stuff
    box = (abs(data['lat0'] - 45) <1.5) & (abs(data['lon0'] - 6) < 1.5)
    data = data[box]
    # st.write('Post-fitering:', data.describe())

    return data


def map(data, lat, lon, zoom, maptype):
    if maptype == 'takeoff':
        coords = '[lon0, lat0]'
    elif maptype == 'landing':
        coords = '[lon1, lat1]'
    else:
        raise ValueError(f'"maptype" should be one pof ["takeoff", "landing"], got "{maptype}".')

    st.pydeck_chart(pdk.Deck(
        map_provider="mapbox",
        map_style=pdk.map_styles.SATELLITE,
        # map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=data,
                get_position=coords,
                radius=1000,
                elevation_scale=4,
                elevation_range=[0, 10],
                auto_highlight=True,
                pickable=True,
                extruded=True,
                coverage=0.6,
            ),

        ],
        tooltip={"html": f"<b>{maptype}s:</b> {{elevationValue}}", "style": {"color": "white"}},

    ))

# Filter data for specific flight durations, cache
@st.experimental_memo
def filterdata(df, min_duration_minutes):
    return df[df["duration"] >= min_duration_minutes * 60]

data = load_data()

# Top section layout
row1_1, row1_2 = st.columns((2, 3))

# See if there's a query param in the url (e.g. ?min_duration_minutes=2)
# This allows you to pass a stateful url to someone with a specific duration selected,
# e.g. https://share.streamlit.io/streamlit/demo-uber-nyc-pickups/main?pickup_hour=2
if not st.session_state.get("url_synced", False):
    try:
        min_duration_minutes = int(st.experimental_get_query_params()["min_duration_minutes"][0])
        st.session_state["min_duration_minutes"] = min_duration_minutes
        st.session_state["url_synced"] = True
    except KeyError:
        pass

# If the slider changes, update the query param
def update_query_params():
    min_duration_minutes = st.session_state["min_duration_minutes"]
    st.experimental_set_query_params(min_duration_minutes=min_duration_minutes)


with row1_1:
    st.title("Paragliding takeoff and landing sites")
    min_duration_minutes = st.slider(
        "Select minimum flight duration in minutes", 0, 1000, key="min_duration_minutes", on_change=update_query_params
    )


with row1_2:
    st.write(
        """
    ##
    Looking at take off and landing coordinates of FFVL's IGC tracks, entered in [Coupe Fédérale de Distance](https://parapente.ffvl.fr/cfd).
    Takoff and landing coordinates are assumed to be the first and last values of the tracks.
    """
    )

# Middle section page layout
row2_1, row2_2 = st.columns((2,2))

# Setting start location and zoom level
st_hilaire = [45.3068009, 5.8878119]
zoom_level = 9

with row2_1:
    st.write(
        f"""**Takeoff**"""
    )
    map(filterdata(data, min_duration_minutes), *st_hilaire, zoom_level, maptype='takeoff')

with row2_2:
    st.write("**Landing**")
    map(filterdata(data, min_duration_minutes), *st_hilaire, zoom_level, maptype='landing')
