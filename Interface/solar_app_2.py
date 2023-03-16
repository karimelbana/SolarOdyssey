import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
import base64
from PIL import Image
from SatImage import get_sat_image_model, initialize_api, create_bounding_box, \
    aggregator
from dotenv import load_dotenv
import os
import requests
import tempfile
from io import BytesIO
from leafmap import ipyleaflet as leafmap



####variable for breaks in f-string
nl = '\n'
path = os.path.abspath(os.path.dirname(__file__))
# Load Logo
with open(os.path.join(path, "icon.svg"), "r") as f:
    svg_content = f.read()

# Encode the SVG content using base64
encoded_svg = base64.b64encode(svg_content.encode()).decode()

# Set Page config
st.set_page_config(
        page_title="SolarOdyssey",
        page_icon=f"data:image/svg+xml;base64,{encoded_svg}",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://chat.openai.com',
            'Report a bug': "https://chat.openai.com",
            'About': "# cool app, eh?"
        }
)


# Place Marker
# Define a function to place a marker on the map
def place_marker(m):
    # Remove any previous marker on the map
    #m.remove_last_layer()

    # Place a new marker at the current coordinates
    marker = leafmap.Marker(location=([st.session_state['coordinates'][0],
                                       st.session_state['coordinates'][1]]))
    m.add_layer(marker)
    return m




# Maps
@st.cache_resource
def get_map():
    # # Create a MapBox map using folium
    # map = folium.Map(location=center_map,
    #                 zoom_start=st.session_state['zoom'],
    #                 scrollWheelZoom=True,
    #                 tiles="OpenStreetMap")
    # tiles_url = 'http://www.google.com/maps/vt/lyrs=s&x={x}&y={y}&z={z}'
    # tiles_attribution = 'Map data © Google'

    map = leafmap.Map(center=st.session_state['center'],
                      zoom=st.session_state['zoom'],
                      height=500,
                      minimap_control=False,
                      measure_control=False,
                      draw_control=False,
                      scrollWheelZoom=False,
                      layers_control=False)  # center on Nigeria
    #tile_layer = leafmap.basemaps(api_key='AIzaSyDpmsyQ4Cr78zxpdF03qPK7fIKzbZ6LXpk')
    #map.add_layer(tile_layer)


    try:
        map = place_marker(map)
    except:
        pass

    return map


def init_api():
    session = initialize_api(dict(st.secrets['GCP']))
    Project = st.secrets['PROJECT']
    return session, Project

def main():

    # Logo loading
    try:
        logo = Image.open(os.path.join(path,'SolarOdyssey_Logo.png'))
    except FileNotFoundError:
        logo = Image.open(os.path.join(path,'SolarOdyssey_Logo.png'))

    # Init Variables
    default_values = {'markers': [],
                    'center': [9.082000, 8.675300],
                    'zoom': 6,
                    'click_count': 0,
                    'coordinates': None,
                    'session': None,
                    'Project': None}

    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value


    session, Project = init_api()

    # Sidebar
    st.sidebar.image(logo, use_column_width=True,
                     output_format='PNG',
                     width=0.5
                     )
    st.sidebar.title("Energy Prediction Demo")
    st.sidebar.markdown(
    """
     \n
    Our project uses satellite images to predict energy demand in rural villages. \n
    Join us in our mission to bring clean and sustainable energy to these communities.
    \n\n\n\n
    """
    )

    st.sidebar.info(
    """
    - [GitHub Repo](https://github.com/karimelbana/SolarOdyssey)
    - [Nigeria - Rural Electrification](http://rrep-nigeria.integration.org/#)
    """
    )

    # Display a map where users can select an area
    m = get_map()
    st.map(m)
    #absasda = m.to_streamlit(scrolling=True, bidirectional=True)

    try:
        st.session_state["coordinates"] = m.st_last_click(m)
        place_marker(m)
    except:
        pass


    # Display the message and the coordinates
    try:
        st.write(f"Selected latitude: {st.session_state['coordinates'][0]}")
        st.write(f"Selected longitude: {st.session_state['coordinates'][1]}")
    except:
        st.write("You have not selected any coordinates yet.")
        st.write("Do so by clicking anyhwere on the map!")


    #Create a button that users can click to obtain the satellite image and NDVI calculation
    if st.button("Get Satellite Image and Predict"):


        # Divide the app layout into two columns
        col1, col2 = st.columns(2)

        with col1:

            model_load_state = st.info("Loading Satellite Image...")

            model_load_state.empty()
            url = "https://solar-api-m6bgenzluq-ew.a.run.app/predict"
            filename = get_sat_image_model(session, Project, st.session_state["coordinates"][0], st.session_state["coordinates"][1])
            files = {"file": ("image.png", open(filename, "rb"), filename)}
            response = requests.post(url, files=files)

            if response.status_code == 200:
                prediction = response.json()
                st.header(f'Energy Demand Prediction:')
                st.header(f'{prediction} kW/Day')

            else:
                st.header(f"Error: {response.text}")

            image = Image.open(filename)
            st.image(image, width = 300)

        with col2:

            data_load_state = st.info("Loading Socio-Economic Data...")
            ### Displaying demographic data of the selected bounding_box
            bounding_box, polygon = create_bounding_box(st.session_state["coordinates"][0], st.session_state["coordinates"][1],"display")


            ### Displaying demographic data of the selected bounding_box
            summary = aggregator(polygon)
            data_load_state.empty()
            st.markdown(f" ## Demographics of the selected frame{nl}")
            st.dataframe(summary)


if __name__ == '__main__':
    main()
