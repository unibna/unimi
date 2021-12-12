FROM python:slim-buster

# identify the working folder
WORKDIR unimi/

# install dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy source code to image
COPY . .
# identify public port
EXPOSE 8000/tcp
# run program
CMD ["python3","manage.py","runserver","0.0.0.0:8000"]