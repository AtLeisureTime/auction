#!/usr/bin/env bash
python /code/auction/manage.py makemigrations
python /code/auction/manage.py migrate

if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    python /code/auction/manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
fi

python /code/auction/manage.py collectstatic --noinput

