import streamlit as st
import altair as alt ########################
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
#@st.cache_resource
def get_map(center_map):

    # Create a MapBox map using folium
    map = folium.Map(location=center_map,
                    zoom_start=st.session_state['zoom'],
                    scrollWheelZoom=False,
                    tiles="OpenStreetMap")
    tiles_url = 'http://www.google.com/maps/vt/lyrs=s&x={x}&y={y}&z={z}'
    tiles_attribution = 'Map data © Google'
    folium.TileLayer(name="Google Maps Satellite",
                     tiles=tiles_url,
                     attr=tiles_attribution).add_to(map)
    folium.LayerControl(position="bottomleft").add_to(map)

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

    load_dotenv()

    session, Project = init_api()

    # Sidebar
    st.sidebar.image(logo, use_column_width=True, output_format='PNG', width=0.5)
    st.sidebar.title("Energy Prediction Demo")
    st.sidebar.markdown(
    """
     \n
    Our project uses satellite images to predict energy demand in rural villages. \n
    This is proof of concept, showcasing the possibilities of Machine Learning for adressing the challenges we face today.
    \n\n\n\n
    """
    )

    st.sidebar.info(
    """
    - [GitHub Repo](https://github.com/karimelbana/SolarOdyssey)
    - [Nigeria - Rural Electrification](http://rrep-nigeria.integration.org/#)
    """
    )



    col1, col2 = st.columns(2, gap="large")

    with col1:

        # Display a map where users can select an area
        m = get_map(st.session_state["center"])

        output = st_folium(

                                m,
                                center=st.session_state["center"],
                                zoom=st.session_state["zoom"],
                                key="NigeriaMap",
                                height=400,
                                width=600
                            )


        try:
            # Set the value of 'coordinates'
            st.session_state['coordinates'] = [output['last_clicked']['lng'],output['last_clicked']['lat']]
        except:
            st.session_state['coordinates'] = None
    with col2:
        try:
            # Display the message and the coordinates
            if st.session_state['coordinates']:

                st.header("Selected Coordinates:")
            st.subheader(f"Latitude: {st.session_state['coordinates'][1]}")
            st.subheader(f"Longitude: {st.session_state['coordinates'][0]}" )
        except:
            st.header("Click anywhere to select coordinates!")

    left, middle, right = st.columns(3)
    col3, col4 = st.columns(2, gap="large")
    with middle:
        #Create a button that users can click to obtain the satellite image and NDVI calculation
        if st.button("Predict Energy Demand And Load Data"):


            with col3:
                model_load_state = st.info(f"Loading Satellite Image...")


                filename = get_sat_image_model(session, Project,st.session_state['coordinates'][0],st.session_state['coordinates'][1])
                image = Image.open(filename)
                url = "https://solar-api-m6bgenzluq-ew.a.run.app/predict"
                files = {"file": ("image.png", open(filename, "rb"), filename)}
                response = requests.post(url, files=files)

                if response.status_code == 200:
                    prediction = response.json()
                    if prediction < 0:
                        st.header(f'Energy Prediction: 0 kWh per day')
                    else:
                        st.header(f'Energy Prediction: {prediction} kWh per day')
                else:
                    st.header(f"Error: {response.text}")

                model_load_state.empty()
                image = Image.open(filename)
                st.image(image, width = 300)
            with col4:
                # Add a button to the right column
                data_load_state = st.info(f"Loading Populaton Data...")

                ### Displaying demographic data of the selected bounding_box
                bounding_box, polygon = create_bounding_box(st.session_state['coordinates'][0],st.session_state['coordinates'][1],"display")

                ### Displaying demographic data of the selected bounding_box
                summary = aggregator(polygon)

                summary_df = pd.DataFrame(summary)

                pop_sum = summary_df.loc['sum', 'Population']
                women_sum = summary_df.loc['sum', 'Women']
                children_sum = summary_df.loc['sum', 'Children (<5 years)']
                youth_sum = summary_df.loc['sum', 'Youth (15-24 years)']
                data_load_state.empty()

                st.markdown(f" ## Demographics of the selected frame{nl}")
                st.dataframe(summary)

                source = pd.DataFrame({
                    'Demographic':['General Population', 'Women', 'Men', 'Children (<5 years)',
                        'Youth (15-24 years)'],
                    'Count':[ pop_sum , women_sum,(pop_sum - women_sum),
                        children_sum, youth_sum]})

                chart = alt.Chart(source).mark_bar().encode(
                    alt.X('Demographic',sort=None),
                    alt.Y('Count'),
                    color=alt.Color('Demographic')).properties(width=500,height=400)

                st.altair_chart(chart, theme="streamlit", use_container_width=False)

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
