import requests
from shapely.geometry import Point
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from shapely.geometry import Point, box
import os
from dotenv import load_dotenv
import pandas as pd
import ee
import ee.mapclient
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
from pprint import pprint
import json

def initialize_api():
    # Obtain a private key file for your service account
    load_dotenv()
    SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT")
    KEY = os.getenv("KEY")
    Project = os.getenv("PROJECT")

    #Start an AuthorizedSession
    credentials = service_account.Credentials.from_service_account_file(KEY)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])

    session = AuthorizedSession(scoped_credentials)

    # Get Earth Engine scoped credentials from the service account.
    # Use them to initialize Earth Engine.
    ee_creds = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY)
    ee.Initialize(ee_creds)

    return session, Project


def get_sat_image_model(session, Project, latitude, longitude):

    # Create a square bounding box around the Lat / Lon
    xmin, ymax = create_bounding_box(latitude, longitude, "Model")

    coords = [xmin, ymax]

    # define our computation for API, result will be an Image (formatted -> numbers)
    region = ee.Geometry.Point(coords)

    collection = ee.ImageCollection('COPERNICUS/S2')
    collection = collection.filterBounds(region)
    collection = collection.filterDate('2019-01-01', '2023-02-01')
    image = ee.Image(collection.sort('CLOUD_COVER').first())

    # Create an object that represents the Earth Engine expression graph
    serialized = ee.serializer.encode(image)

    # Create the desired projection (WGS84) at the desired scale (10 meters for Sentinel-2)
    proj = ee.Projection('EPSG:4326').atScale(5).getInfo()

    # Get scales out of the transform.
    scale_x = proj['transform'][0]
    scale_y = -proj['transform'][4]

    # Send the request
    """
    Make a POST request to the computePixels endpoint.
    Note that the request contains the Expression, which is the serialized computation.
    It also contains a PixelGrid. The PixelGrid contains dimensions for the desired output
    and an AffineTransform in the units of the requested coordinate system.
    Here the coordinate system is geographic, so the transform is specified with scale in degrees
    and geographic coordinates of the upper left corner of the requested image patch.
    """

    url = 'https://earthengine.googleapis.com/v1beta/projects/{}/image:computePixels'
    url = url.format(Project)

    response = session.post(
    url=url,
    data=json.dumps({
        'expression': serialized,
        'fileFormat': 'PNG',
        'bandIds': ['B4','B3','B2'],
        'grid': {
        'dimensions': {
            'width': 512,
            'height': 512
        },
        'affineTransform': {
            'scaleX': scale_x,
            'shearX': 0,
            'translateX': coords[0],
            'shearY': 0,
            'scaleY': scale_y,
            'translateY': coords[1]
        },
        'crsCode': 'EPSG:4326',
        },
        'visualizationOptions': {'ranges': [{'min': 0, 'max': 3000}]},
    })
    )

    image_content = response.content

    # if mode == 'Model':
    #     # Generate the filename
    #     filename = "temp/{},{}.png".format(latitude,longitude)
    #     # Save the image data to file
    #     with open(filename, "wb") as f:
    #         f.write(image_content)
    # else:
    # Generate the filename
    filename = "Interface/temp/{},{}.png".format(latitude,longitude)
    with open(filename, "wb") as f:
        f.write(image_content)
        return filename

def create_bounding_box(longitude, latitude, mode):
    # Define the point and square side length
    point = Point(longitude, latitude)
    side_length = 0.02  # 0.01 degrees is approximately 1 km at the equator

    # Create a square bounding box around the point
    xmin = point.x - side_length / 2
    xmax = point.x + side_length / 2
    ymin = point.y - side_length / 2
    ymax = point.y + side_length / 2

    # Create bbox
    bboxes = []
    bboxes.append([(xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin), (xmax, ymin)])

    if mode == 'Model':
        return xmin, ymax
    else:
        return bboxes



def aggregator(bboxes):

    df = pd.read_csv('df_eighth.csv')
    ###########

    # Transform csv in GeoDataFrame from the DataFrame by specifying the geometry column
    gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(
    df['longitude'],
    df['latitude']
    ))

    # Create a Polygon object for the area of interest

    polygon = Polygon(bboxes)
    # Filter points that fall within the polygon
    points_within_polygon = gdf_points[gdf_points.within(polygon)]
    summary_stats = points_within_polygon.agg({'Population': ['sum'],
                                           'Women': ['sum'],
                                           'Children (<5 years)':['sum'],
                                           'Youth (15-24 years)':['sum']}
                                            ).round().astype(int)
    return summary_stats
