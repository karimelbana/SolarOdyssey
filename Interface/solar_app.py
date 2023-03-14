import streamlit as st
import pandas as pd
import plotly.express as px
from folium.plugins import Draw
from streamlit_folium import st_folium
import folium
import base64
from PIL import Image
from SatImage import get_sat_image_model, initialize_api, create_bounding_box
from dotenv import load_dotenv
import os
import requests
import tempfile

# Load Logo
with open("icon.svg", "r") as f:
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

    bounding_box = []
    # Define the bounding box coordinates
    if st.session_state['coordinates'] is not None:
        bounding_box = create_bounding_box(st.session_state['coordinates'][1], st.session_state['coordinates'][0], "Display")

        # Add the bounding box to the map
        folium.Polygon(
            locations=bounding_box,
            popup="2km x 2km Bounding Box",
            color='red',
            fill=False
        ).add_to(map)

    return map

@st.cache_data
def init_api():
    session, Project = initialize_api()
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

    # st.markdown(
    #     """
    #     <style>
    #     #root > div:nth-child(1) > div > div.css-1d6fzt {
    #         display: none;
    #     }
    #     </style>
    #     """,
    #     unsafe_allow_html=True
    # )

    # Sidebar
    st.sidebar.image(logo, use_column_width=True, output_format='PNG', width=0.5)
    st.sidebar.title("Energy Prediction Demo")
    st.sidebar.markdown(
    """
    Welcome to SolarOdyssey! \n
    Our project uses satellite images to predict energy demand in rural villages. \n
    Join us in our mission to bring clean and sustainable energy to these communities.
    \n\n\n\n
    """
    )
    # """"
    # Welcome to SolarOdyssey!
    # Our mission is to bring clean and sustainable energy to rural villages.
    # Using advanced satellite imaging technology and machine learning algorithms,
    # we have developed a model that can accurately predict the energy demand of a village.
    # Our innovative approach is designed to help these communities meet their energy needs while minimizing their impact on the environment.
    # Join us on this journey as we work towards a brighter future for everyone.
    # """
    st.sidebar.info(
    """
    - [GitHub Repo](https://github.com/karimelbana/SolarOdyssey)
    - [Nigeria - Rural Electrification](http://rrep-nigeria.integration.org/#)
    """
    )

    map_placeholder = st.empty()



    # Display a map where users can select an area
    m = get_map(st.session_state["center"])

    # Display the map
    with map_placeholder.container():
        output = st_folium(
                            m,
                            center=st.session_state["center"],
                            zoom=st.session_state["zoom"],
                            key="NigeriaMap",
                            height=600,
                            width=800
                        )
        #st.write(output)

    # try:
    #     if len(output["all_drawings"]) == 1:

    #         try:
    #             if output["last_active_drawing"]["geometry"]["type"] == "Point":
    #                 st.session_state['coordinates'] = output["last_active_drawing"]["geometry"]["coordinates"]
    #         except TypeError:
    #             st.session_state['coordinates'] = None

    #         # Reset the map to its initial state
    #         m = get_map()

    #     else:
    #         st.write("Please make sure that you only have one Point/Marker on the map.")
    # except:
    #     st.write("")


    # Display the message and the coordinates
    st.text("You have selected the following coordinates:")
    st.write(st.session_state['coordinates'])

    # Divide the app layout into two columns
    col1, col2 = st.columns(2)

    #Create a button that users can click to obtain the satellite image and NDVI calculation
    if col1.button("Get Satellite Image and Predict"):

        model_load_state = st.info(f"Loading Satellite Image...")

        # Set the value of 'coordinates'
        st.session_state['coordinates'] = [output['last_object_clicked']['lng'],output['last_object_clicked']['lat']]

        filename = get_sat_image_model(session, Project,st.session_state['coordinates'][0],st.session_state['coordinates'][1])
        image = Image.open(filename)

        model_load_state.empty()
        expander = st.expander("See explanation")
        expander.image(image, caption="Satellite Image", use_column_width=True)

        # Prediction
        wagon_cab_api_url = 'https://solarodyssey-api-m6bgenzluq-uc.a.run.app/predict'
        response = requests.get(wagon_cab_api_url, filename)

        prediction = response.json()

        st.header(f'Fare amount: {prediction}')

    # Add a button to the right column
    if col2.button('Right Button'):
        st.write('Right button clicked!')



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
