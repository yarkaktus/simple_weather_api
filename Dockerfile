FROM python:3.7-alpine

RUN mkdir -p /app/
WORKDIR app

ADD main.py /app/
ADD requirements.txt /app/

EXPOSE 8000

RUN pip install -r requirements.txt
CMD [ "python", "/app/main.py" ]