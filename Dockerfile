FROM python:3.12.3

WORKDIR /src

COPY ./model /src/app/model

COPY ./data/background_data.csv /src/app/data/background_data.csv

COPY ./endpoint2.py /src/app

COPY ./utility.py /src/app

COPY ./requirements.txt /src

RUN pip install -r /src/requirements.txt

# ENV PYTHONPATH

CMD ["python", "./app/endpoint2.py", "--port", "5500"]