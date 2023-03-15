import requests
from io import BytesIO

url = "http://localhost:8000/predict"
files = {"file": ("image.png", open("10228.png", "rb"), "10228.png")}
response = requests.post(url, files=files)

if response.status_code == 200:
    prediction = response.json()
    print(prediction)
else:
    print("Error:", response.text)



# url = "http://localhost:8000/predict"
# file_path = "10228.png"

# with open(file_path, "rb") as image_file:
#     files = {"file": ("image.png", BytesIO(image_file.read()), file_path)}
#     response = requests.post(url, files=files)



# # file = "10228.png"

# with open(file, "rb") as f:
#     file_bytes = f.read()


# wagon_cab_api_url = 'http://localhost:8000/predict'
# response = requests.post(wagon_cab_api_url, files={"file": ("10228.png", BytesIO(file_bytes))})

# if response.status_code == 200:
#     image_shape = response.json()
#     print("Preprocessed image shape:", image_shape)
# else:
#     print("Error:", response.content)
