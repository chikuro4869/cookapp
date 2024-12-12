
FROM python:3.9

RUN apt-get update && apt-get install -y sqlite3 && apt-get install -y libsqlite3-dev

WORKDIR /usr/src

COPY ./apps usr/src/apps
COPY ./local.sqlite /usr/src/local.sqlite
COPY ./requirements.txt /usr/src/requirements.txt
COPY ./apps/detector/best11month.pt /usr/src/best11month.pt


RUN pip install --upgrade pip


RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118


RUN pip install --default-timeout=100 -r requirements.txt


RUN echo "building..."

ENV FLASK_APP=apps.app:create_app('local')
ENV IMAGE_URL=/storage/images/
ENV PORT=8080


EXPOSE 8080 


CMD ["flask", "run", "-h", "0.0.0.0", "-p", "8080"] 
