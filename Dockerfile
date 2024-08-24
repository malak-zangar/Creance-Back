FROM python:3.10

EXPOSE 5000
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

CMD gunicorn --bind 0.0.0.0:5000 --timeout 120 -w 1 -k gevent app:app
