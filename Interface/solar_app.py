import streamlit as st
import pandas as pd
from folium.plugins import Draw
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
@st.cache_resource
def get_map(center_map):

    # Create a MapBox map using folium
    map = folium.Map(location=center_map,
                    zoom_start=st.session_state['zoom'],
                    scrollWheelZoom=True,
                    tiles="OpenStreetMap")
    Draw(export=True).add_to(map)
    tiles_url = 'http://www.google.com/maps/vt/lyrs=s&x={x}&y={y}&z={z}'
    tiles_attribution = 'Map data © Google'

# Start Fixes
    # bounding_box = []
    # # Define the bounding box coordinates
    # if st.session_state['coordinates'] is not None:
    #     bounding_box = create_bounding_box(st.session_state['coordinates'][1], st.session_state['coordinates'][0], "Display")

    #     # Add the bounding box to the map
    #     folium.Polygon(
    #         locations=bounding_box,
    #         popup="2km x 2km Bounding Box",
    #         color='red',
    #         fill=False
    #     ).add_to(map)


    return map #, bounding_box


def init_api():
    session = initialize_api(dict(st.secrets['GCP']))
    Project = st.secrets['PROJECT']
    return session, Project

def main():

    # Logo loading
    try:
        logo = Image.open('SolarOdyssey_Logo.png')
    except FileNotFoundError:
        logo = Image.open('SolarOdyssey_Logo.png')

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



# Fix 2

    # Display a map where users can select an area
    m = get_map(st.session_state["center"])

# Fix 3
    output = st_folium(

                            m,
                            center=st.session_state["center"],
                            zoom=st.session_state["zoom"],
                            key="NigeriaMap",
                            height=600,
                            width=800
                        )


    try:
        # Set the value of 'coordinates'
        st.session_state['coordinates'] = [output['last_object_clicked']['lng'],output['last_object_clicked']['lat']]
    except:
        st.session_state['coordinates'] = None

    # Display the message and the coordinates
    st.text("You have selected the following coordinates:")
    st.write(st.session_state['coordinates'])

    # Divide the app layout into two columns
    col1, col2 = st.columns(2)

    #Create a button that users can click to obtain the satellite image and NDVI calculation
    if col1.button("Get Satellite Image and Predict"):

# Fix 4
        # Set the value of 'coordinates'
        st.session_state['coordinates'] = [output['last_object_clicked']['lng'],output['last_object_clicked']['lat']]


        model_load_state = st.info(f"Loading Satellite Image...")


        filename = get_sat_image_model(session, Project,st.session_state['coordinates'][0],st.session_state['coordinates'][1])
        image = Image.open(filename)

        model_load_state.empty()
        expander = st.expander("Show Satellite Image")
        expander.image(image, caption="PLACEHOLDER LAT LON", use_column_width=True)

        url = "https://solar-api-m6bgenzluq-ew.a.run.app/predict"
        files = {"file": ("image.png", open(filename, "rb"), filename)}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            prediction = response.json()
            st.header(f'Energy Prediction: {prediction}')
        else:
            st.header(f"Error: {response.text}")


    # Add a button to the right column
    if col2.button('Display Socio-Economic Data'):

        ### Displaying demographic data of the selected bounding_box
        summary = aggregator(bounding_box)

        #summary_df = pd.DataFrame(summary)

        #pop_sum = summary_df.loc['sum', 'Population']
        #women_sum = summary_df.loc['sum', 'Women']
        #children_sum = summary_df.loc['sum', 'Children (<5 years)']
        #youth_sum = summary_df.loc['sum', 'Youth (15-24 years)']
        #
        #Print the values to the console
        #
        # #st.markdown(f" ## Demographics of the selected frame{nl}"
        # f" #### Overall Population: {pop_sum}{nl}"
        # f" #### Women: {women_sum} {nl}"
        # f" ##### in percentage : {((women_sum / pop_sum)*100).round(1)}% {nl}"
        # f" #### Children below the Age of 5 years: {children_sum} {nl}"
        # f" ##### in percentage : {((children_sum / pop_sum)*100).round(1)} % {nl}"
        # f" #### Youth (age 15 to 24): {youth_sum} {nl}"
        # f" ##### in percentage : {((youth_sum / pop_sum)*100).round(1)} % {nl}")
        #
        st.markdown(f" ## Demographics of the selected frame{nl}")
        st.dataframe(summary)


if __name__ == '__main__':
    main()










# if st.session_state['coordinates'] is not None:
#     st.session_state['coordinates'] = output["last_active_drawing"][0]["geometry"]["coordinates"]
#     st.write(st.session_state['coordinates'])










    #m.add_child(folium.ClickForMarker(popup="Click the map to select pickup and dropoff locations", on_click=marker_check))



    # Load GeoJSON data
    # geojson_data = pd.read_json('/Users/arnoud/Documents/Test/ngaadmbndaadm1osgof20161215.geojson')


    # Add the GeoJSON data to the map
    # folium.GeoJson(geojson_data).add_to(m)



# # Set up MapBox access token
# mapbox_access_token = "pk.eyJ1IjoiYWRlaGFhbjExIiwiYSI6ImNsZXNiaHQ3NzBpMmgzd24xYjFneXg3dGoifQ.sivDuH_HS-T4F6f8UW8pcw"


# click_count = 0
# pop_name = ""
# # Define the function to handle map clicks
# def on_map_click(e):
#     global pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude, click_count

#     if click_count == 0:
#         # First click is the pickup location
#         pop_name = "Pickup"
#         pickup_latitude, pickup_longitude = e.latlng
#         folium.Marker(location=e.latlng, popup="Pickup location").add_to(m)


#         # Update the value of the pickup latitude input field
#         pickup_latitude = st.sidebar.number_input("Pickup latitude", value=pickup_latitude)
#         pickup_longitude = st.sidebar.number_input("Pickup longitude", value=pickup_longitude)
#         st.experimental_rerun()
#         click_count += 1

#     elif click_count == 1:
#         pop_name = "Dropoff"
#         # Second click is the dropoff location
#         dropoff_latitude, dropoff_longitude = e.latlng
#         folium.Marker(location=e.latlng, popup="Dropoff location").add_to(m)


#         # Update the value of the dropoff latitude input field
#         dropoff_latitude = st.sidebar.number_input("Dropoff latitude", value=dropoff_latitude)
#         dropoff_longitude = st.sidebar.number_input("Dropoff longitude", value=dropoff_longitude)
#         st.experimental_rerun()
#         click_count += 1

# # # Add a click listener to the map
# # m.add_child(folium.ClickForMarker(popup="Click the map to select pickup and dropoff locations", on_click=on_map_click))
