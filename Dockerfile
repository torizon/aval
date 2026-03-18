FROM python:3.12

RUN mkdir -p /aval
COPY . /aval
WORKDIR /aval

RUN pip install -r ./requirements.txt
RUN pip install black

RUN apt-get update \
    && apt-get install -y \
        curl \
        jq \
        lsof \
        unzip \
    && rm -rf /var/lib/apt/lists/*

COPY aws_database/install-ssm.sh /tmp/install-ssm.sh
RUN chmod +x /tmp/install-ssm.sh \
    && /tmp/install-ssm.sh \
    && rm -f /tmp/install-ssm.sh

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
