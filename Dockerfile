FROM python:latest AS test

RUN mkdir -p /aval
COPY . /aval
WORKDIR /aval

RUN pip install -r ./requirements.txt
