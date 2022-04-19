FROM python:3.10-slim
ADD app.py /
RUN pip install paho-mqtt
CMD [ "python", "./app.py" ]
