FROM python:3.6-alpine

MAINTAINER zzz <solo-in-dark@abchina.com>

ENV TZ Asia/Shanghai

WORKDIR /app

COPY ./requirements.txt .

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories

RUN apk add musl-dev gcc    && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    apk del gcc musl-dev

COPY . .

EXPOSE 8000

ENTRYPOINT [ "python", "gsxt_spider_starter.py" ]