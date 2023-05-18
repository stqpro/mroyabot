# syntax=docker/dockerfile:1

FROM python:3.10-slim

WORKDIR /app

COPY ./web/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./web .

CMD [ "python3", "bot.py"]
