FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY admin/application.py ./application.py
COPY admin/configuration.py ./configuration.py
COPY admin/models.py ./models.py
COPY admin/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt


# ENTRYPOINT ["echo" , "hello world"]
# ENTRYPOINT ["sleep" , "1200"]
ENTRYPOINT ["python" , "./application.py"]
