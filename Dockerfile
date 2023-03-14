# tensorflow base-images are optimized: lighter than python-buster + pip install tensorflow
FROM tensorflow/tensorflow:2.10.0
# OR for apple silicon, use this base image instead
#FROM armswdev/tensorflow-arm-neoverse:r22.09-tf-2.10.0-eigen


RUN pip install --upgrade pip

COPY requirements.txt requirements.txt
COPY api api

COPY Interface Interface
COPY setup.py setup.py
RUN pip install .

CMD uvicorn api.fast_api:app --host 0.0.0.0 --port $PORT
