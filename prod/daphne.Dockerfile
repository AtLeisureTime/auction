# Pull official base Python Docker image
FROM python:3.10.6

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get install -y gcc

# Set work directory
WORKDIR /code

# Install dependencies
RUN pip install --upgrade pip

COPY requirements_prod.txt /code/
RUN pip install -r requirements_prod.txt

# Copy the Django project
COPY . /code/

RUN chmod +x ./wait-for-it.sh
