FROM python:slim-buster

WORKDIR /unimi/

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . /unimi/

EXPOSE 8000/tcp

CMD ["python3", "manage.py", "runserver", "127.0.0.1:8000"]