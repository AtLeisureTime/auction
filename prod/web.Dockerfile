FROM python:3.10.6

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get install -y gcc

RUN pip install --upgrade pip

WORKDIR /code
RUN mkdir /tmp/auction
VOLUME [ "/code", "/tmp/auction" ]

COPY ./prod/requirements_prod.txt /tmp/requirements_prod.txt
RUN pip install -r /tmp/requirements_prod.txt

ENV PYTHONPATH "${PYTHONPATH}:/code/auction"
