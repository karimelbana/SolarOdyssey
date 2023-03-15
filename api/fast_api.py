import pandas as pd
import numpy as np
from PIL import Image
from tensorflow.keras.applications.densenet import preprocess_input as preprocess_input_densenet
from tensorflow.keras.models import load_model
from io import BytesIO
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


#Optional, good practice for dev purposes. Allow all middlewares .
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 💡 Preload the model to accelerate the predictions
model_path = "Interface/the_best_model.h5"
app.state.model = load_model(model_path)


# Takes in a file and returns a prediction
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()

    # Read the bytes back into an image format, then convert to a numpy array
    image = np.array(Image.open(BytesIO(contents)))

    #Preprocess the image
    image_preproc = preprocess_input_densenet(image)

    to_predict = np.expand_dims(image_preproc, axis=0)

    # Load model
    model = app.state.model
    assert model is not None

    # Make prediction
    y_pred = model.predict(to_predict)

    return round(float(y_pred),2 )

@app.get("/")
def root():
    return dict(greeting="Aloha")
