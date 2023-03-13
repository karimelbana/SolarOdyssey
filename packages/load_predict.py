import pandas as pd
import numpy as np

from PIL import Image
import matplotlib.pyplot as plt

from os import walk
import os

from sklearn.model_selection import train_test_split

from tensorflow.keras.applications.densenet import preprocess_input as preprocess_input_densenet
from tensorflow.keras.models import load_model

def predict(model_path, user_image_path):

    #process user image
    user_image_np = np.array(np.array(Image.open(user_image_path)))
    #plt.imshow(user_image)
    user_image_preproc = preprocess_input_densenet(user_image_np)
    to_predict = np.expand_dims(user_image_preproc, axis=0)
    print('Image is processed')

    #load model
    model = load_model(model_path, compile=False)
    print('Model is loaded')

    y_pred = model.predict(to_predict)
    print(f'Predicted daily energy demand of selected area is: {round(y_pred[0][0],0)} kWh/day')

    return round(y_pred[0][0],1)

if __name__ == "__main__":
    predict('../models/RegressionDensenet121/model_val_loss_2829.130126953125.h5', '../user_image/41819.png')
    #print("A python package that loads a pre-trained model to predict the energy demand of selected area in Nigeria using its sattelite image!")
