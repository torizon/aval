FROM python:latest AS test

RUN mkdir -p /aval
COPY . /aval
WORKDIR /aval

RUN pip install -r ./requirements.txt

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
