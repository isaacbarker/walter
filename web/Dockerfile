FROM python:3-alpine3.22

WORKDIR /walter

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "main.py"]