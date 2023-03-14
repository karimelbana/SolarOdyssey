import pandas as pd
import numpy as np
from PIL import Image
from tensorflow.keras.applications.densenet import preprocess_input as preprocess_input_densenet
from tensorflow.keras.models import load_model

from fastapi import FastAPI
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

@app.get("/predict")
def predict(filepath: str):  # image filepath

    # Process user image
    user_image_np = np.array(np.array(Image.open(filepath)))

    user_image_preproc = preprocess_input_densenet(user_image_np)
    to_predict = np.expand_dims(user_image_preproc, axis=0)

    # Load model
    model = app.state.model
    assert model is not None

    # Make prediction
    y_pred = model.predict(to_predict)

    return round(y_pred[0][0],1)

@app.get("/")
def root():
    return dict(greeting="Aloha")
