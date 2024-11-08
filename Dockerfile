FROM python:3.8-slim

RUN apt-get -y update && \
    apt-get install --no-install-recommends -y \
    build-essential \
    manpages-dev \
    procps \
    python3-dev \
    python3-pip \
    && \
    rm -rf /var/lib/apt/lists/*

COPY webhook_utils.py ./
COPY requirements.txt ./
COPY secret_utils.py ./
COPY functions.py ./
COPY logger.py ./
COPY models.py ./
COPY main.py ./


RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

RUN rm -frv ./requirements.txt
ENV script main.py
CMD python ${script}