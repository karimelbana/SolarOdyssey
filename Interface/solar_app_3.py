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
import leafmap

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
            'Get Help': 'https://www.chat.openai.com',
            'Report a bug': "https://www.chat.openai.com",
            'About': "# cool app, eh?"
        }
)



# Maps
#@st.cache_resource
def get_map(center_map):
    if st.session_state['Map'] is not None:
        return
    # Create a MapBox map using folium
    map = folium.Map(location=center_map,
                    zoom_start=st.session_state['zoom'],
                    scrollWheelZoom=False,
                    tiles="OpenStreetMap")
    tiles_url = 'http://www.google.com/maps/vt/lyrs=s&x={x}&y={y}&z={z}'
    tiles_attribution = 'Map data © Google'
    folium.TileLayer(tiles=tiles_url,
                     attr=tiles_attribution).add_to(map)
    folium.LayerControl().add_to(map)
    st.session_state['Map'] = map
    return st.session_state['Map']

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
                    'Project': None
                    ,'Map' : None}

    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

    load_dotenv()

    session, Project = init_api()

    # Sidebar
    st.sidebar.image(logo, use_column_width=True, output_format='PNG', width=0.5)
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
    get_map(st.session_state["center"])

    try:
        st.session_state["coordinates"] = output["last_clicked"]
        marker = folium.Marker(location=[st.session_state["coordinates"]["lat"], st.session_state["coordinates"]["lng"]])
        st.session_state['Map'].add_child(marker)

    except:
        pass
    output = st_folium(     st.session_state['Map'],
                            width=800,
                            height=500
                        )


    # Display the message and the coordinates
    try:
        st.write(f"Selected latitude: {st.session_state['coordinates']['lat']}")
        st.write(f"Selected longitude: {st.session_state['coordinates']['lng']}")
    except:
        st.write("You have not selected any coordinates yet.")
        st.write("Do so by clicking anyhwere on the map!")


    # Divide the app layout into two columns
    col1, col2 = st.columns(2)

    #Create a button that users can click to obtain the satellite image and NDVI calculation
    if col1.button("Get Satellite Image and Predict"):

        model_load_state = st.info(f"Loading Satellite Image...")


        filename = get_sat_image_model(session, Project, st.session_state["coordinates"]['lat'], st.session_state["coordinates"]["lng"])
        image = Image.open(filename)

        model_load_state.empty()
        url = "https://solar-api-m6bgenzluq-ew.a.run.app/predict"
        files = {"file": ("image.png", open(filename, "rb"), filename)}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            prediction = response.json()
            st.header(f'Energy Demand Prediction: {prediction} kW')
        else:
            st.header(f"Error: {response.text}")

        expander = st.expander("Show Satellite Image")
        expander.image(image, caption=f"Latitude {st.session_state['coordinates']['lat']} Longitude {st.session_state['coordinates']['lng']}", use_column_width=True)




    # Add a button to the right column
    if col2.button('Display Socio-Economic Data'):

        ### Displaying demographic data of the selected bounding_box
        bounding_box, polygon = create_bounding_box(st.session_state["coordinates"]["lat"], st.session_state["coordinates"]["lng"],"display")

        ### Displaying demographic data of the selected bounding_box
        summary = aggregator(polygon)

        st.markdown(f" ## Demographics of the selected frame{nl}")
        st.dataframe(summary)


if __name__ == '__main__':
    main()
