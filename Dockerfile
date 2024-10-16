FROM python:3.12 AS test

RUN mkdir -p /aval
COPY . /aval
WORKDIR /aval

RUN pip install -r ./requirements.txt
RUN pip install black

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
