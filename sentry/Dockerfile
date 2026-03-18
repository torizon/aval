FROM python:3.12

RUN mkdir -p /sentry
COPY ./sentry /sentry
COPY ./aws_database /aws_database
WORKDIR /sentry

RUN pip install uv

RUN apt-get update \
    && apt-get install -y \
        curl \
        lsof \
        unzip \
    && rm -rf /var/lib/apt/lists/*

COPY aws_database/install-ssm.sh /tmp/install-ssm.sh
RUN chmod +x /tmp/install-ssm.sh \
    && /tmp/install-ssm.sh \
    && rm -f /tmp/install-ssm.sh
