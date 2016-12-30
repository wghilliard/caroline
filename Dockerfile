FROM ubuntu:latest

RUN apt-get update && apt-get install -y wget python3

RUN wget -P /tmp https://bootstrap.pypa.io/get-pip.py && python3 /tmp/get-pip.py && rm /tmp/get-pip.py

COPY . /opt/caroline

RUN pip3 install --no-cache-dir -r /opt/caroline/requirements.txt

ENTRYPOINT ["python3", "/opt/caroline/core.py"]