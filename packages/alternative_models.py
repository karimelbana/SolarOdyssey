# Mount GDrive
from google.colab import drive
drive.mount('/content/drive')

import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image

from tensorflow.keras import Sequential, layers, models
from tensorflow.keras import optimizers
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers.experimental.preprocessing import Rescaling
from sklearn.model_selection import train_test_split

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input as preprocess_input_vgg16
from tensorflow.keras.preprocessing.image import ImageDataGenerator
#from tensorflow.keras.layers import RandomBrightness
#from tensorflow.keras.layers import RandomContrast

from tensorflow.image import rgb_to_grayscale

from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input as preproc_res


import matplotlib.pyplot as plt

#Put Colab in the context of this challenge
import os
from os import walk


df_masked_cat = pd.read_csv('/content/drive/MyDrive/SolarOdyssey/df_masked_cat.csv')

#fetch images titles as ids
data_path = '/content/drive/MyDrive/SolarOdyssey/rrep_nigeria/data/high_res'
f = []
for (dirpath, dirnames, filenames) in walk(data_path):
    f.extend(filenames)
    break

images_ids = []
for id in filenames:
  id = int(id.strip('.png'))
  images_ids.append(id)
#images_ids

y = []
for id in images_ids:
  #print(id)
  y.append(int(df_masked_cat[df_masked_cat['Id'] == id].Demand.values[0]))
#len(y)

print(f'{len(filenames)} images found and {len(y)} target values are allocated')


def load_sattelite_images(data_path, data_folder, y):
    '''
    loading the images and creating train vlaidate test datasets
    '''

    data_path = data_path
    y = np.array(y)
    imgs = []
    images_path = [os.path.join(data_folder, elt) for elt in os.listdir(os.path.join(data_path)) if elt.find('.png')>0]
    for path in images_path:
        if os.path.exists(path):
            image = Image.open(path)
            #image = image.resize((256, 256))
            imgs.append(np.array(image))

    X = np.array(imgs)
    #print(X.shape)

    X_train, X_sub, y_train, y_sub = train_test_split(X, y, test_size=0.40, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_sub, y_sub, test_size=0.20, random_state=42)

    return X_train, y_train, X_val, y_val, X_test, y_test

#pwd

os.chdir("drive/MyDrive/SolarOdyssey/data")

data_path = '/content/drive/MyDrive/SolarOdyssey/data/high_res'
data_folder = 'high_res'
X_train, y_train, X_val, y_val, X_test, y_test = load_sattelite_images(data_path, data_folder, y)

print('Training, Validation and Test Datasets are generated')

print('Train Datasets Shape:')
print(X_train.shape, np.array(y_train).shape)
print('Validation Datasets Shape:')
print(X_val.shape, np.array(y_val).shape)
print('Test Datasets Shape:')
print(X_test.shape, np.array(y_test).shape)

#plt.imshow(X_train[0])

#Preprocess to match VGG16 or resnet50
model_selected = 'resnet50'

if model_selected == 'vgg16':
  X_train = preprocess_input_vgg16(X_train)
  X_val = preprocess_input_vgg16(X_val)
  X_test = preprocess_input_vgg16(X_test)

elif model_selected == 'resnet50':
  X_train = preproc_res(X_train)
  X_val = preproc_res(X_val)
  X_test = preproc_res(X_test)

#Building the model strucure

#load model
def load_model(model_selected):
    if model_selected == 'vgg16':
      model = Sequential()
      model = VGG16(weights="imagenet", include_top=False, input_shape=X_train[0].shape)
      #print(model.summary())
    elif model_selected == 'resnet50':
      model = Sequential()
      model = ResNet50(weights='imagenet', include_top = False, input_shape=X_train[0].shape)
      #print(model.summary())
    return model

#Retrain the model?
def set_nontrainable_layers(model):
  # Set the first layers to be untrainable
  model.trainable = False
  return model

#adding model layers
def add_last_layers(model):
    '''Take a pre-trained model, set its parameters as non-trainable, and add additional trainable layers on top'''
    base_model = set_nontrainable_layers(model)
    flatten_layer = layers.Flatten()
    dense_layer = layers.Dense(30, activation='relu')
    prediction_layer = layers.Dense(1, activation='linear')
    model_w_layers = models.Sequential([
        #RandomContrast(factor=0.2, seed=None),
        #RandomBrightness(factor=0.2, value_range=(0, 255), seed=None),
        model,
        flatten_layer,
        dense_layer,
        prediction_layer
    ])
    return model_w_layers

#buidling all together
def build_model(model_selected):
  model = load_model(model_selected)
  model_full = add_last_layers(model)
  #opt = optimizers.Adam(learning_rate=1e-4)
  model_full.compile(loss="mse", optimizer='adam', metrics='mae')
  return model_full

#augmentation?
datagen = ImageDataGenerator(
    featurewise_center=False,
    samplewise_center=False,
    featurewise_std_normalization=False,
    samplewise_std_normalization=False,
    zca_whitening=False,
    zca_epsilon=1e-06,
    rotation_range=0,
    width_shift_range=0.0,
    height_shift_range=0.0,
    brightness_range=None,
    shear_range=0.0,
    zoom_range=0.0,
    channel_shift_range=0.0,
    fill_mode='nearest',
    cval=0.0,
    horizontal_flip=False,
    vertical_flip=False,
    rescale=None,
    preprocessing_function=None,
    data_format=None,
    validation_split=0.0,
    interpolation_order=1,
    dtype=None
)

datagen.fit(X_train)

#initiating the model
model = Sequential()
model = load_model(model_selected)
#model.summary()
model_built = build_model(model_selected)
model_built.summary()
es = EarlyStopping(monitor = 'val_loss',
                   patience = 5,
                   verbose = 1,
                   restore_best_weights = True)

print('Model is initiated')

#fitting the model
history = model_built.fit(datagen.flow(X_train, y_train, batch_size=32) \
                          , validation_data=(X_val, y_val), epochs=50, batch_size=16, callbacks=[es])


min_val_loss = round(np.min(history.history['val_loss']))
print('Model converged with min mae: {min_val_loss}')

#exporting the model
model_built.save(f'regression_resnet50_mae: {min_val_loss}.h5')
print(f'Model: regression_resnet50_mae: {min_val_loss}.h5 is exported')

#evaluate the model
#print(model_built.evaluate(X_test, y_test, verbose=1))
#plt.plot(history.history['val_loss'])


#predict
#test = np.expand_dims(X_test[1], axis=0)
#test.shape
#model_built.predict(test)
