FROM python:3.6

RUN pip install python-kucoin slackClient
RUN mkdir /opt/kucoinBot/
COPY . /opt/kucoinBot/
WORKDIR /opt/kucoinBot/

ENTRYPOINT ["python", "bot.py"]
