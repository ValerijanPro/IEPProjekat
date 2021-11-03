FROM python:3

RUN mkdir -p /opt/src/modifikacija
WORKDIR /opt/src/modifikacija

COPY modifikacija/application.py ./application.py
COPY modifikacija/configuration.py ./configuration.py
COPY modifikacija/models.py ./models.py
COPY modifikacija/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt


# ENTRYPOINT ["echo" , "hello world"]
# ENTRYPOINT ["sleep" , "1200"]
ENTRYPOINT ["python" , "./application.py"]
