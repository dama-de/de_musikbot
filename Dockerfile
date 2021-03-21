FROM alpine:3

RUN apk add python3 py3-pip py3-aiohttp

ADD main.py /bot/
ADD requirements.txt /bot/

VOLUME /data
ENV DATA_DIR=/data
WORKDIR /bot

RUN pip install -r requirements.txt
ENTRYPOINT python3 main.py