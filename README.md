# Auction
## Features
* Auction admin can create/modify/delete lots, stakes, users and their profiles.
* Unauthenticated Auction users can
  - view all lots with AuctionState not equal "Draft" using AuctionState filter and description search form ranking lots by search query
  - view stakes made by other users
  - open registration form
* Authenticated Auction user can also
  - make stakes on lots with AuctionState "Started"
  - view stakes made by other users on the lot page in real time without refreshing the page
  - edit their profiles and change their passwords

## Demo video
Auction admin is editing the auction lot and is launching auction for this lot. When admin sets "Not started" AuctionState, 2 jobs are created - start the auction and finish it at specified time. 2 users are making stakes while auction is in progress.
<br />https://user-images.githubusercontent.com/16018457/227154695-2f5de556-1cfb-415c-9c28-691512653251.mp4

Lot edit error validation, auction state transition validation, lots filter by auction state
<br />https://user-images.githubusercontent.com/16018457/227154777-d2872fe0-c290-4280-a221-54111873cd21.mp4

Login by username & email, registration, profile editing, password change forms
<br />https://user-images.githubusercontent.com/16018457/227154828-9295f24a-d3a2-4f9f-a2b3-da6feae97197.mp4

## Tech stack
* Python 3.10
* Django 4.1
* PostgreSQL
* Celery
* RabbitMQ
* Redis
* Channels
* Daphne
* Nginx
* Docker, docker compose

## Run auction

### Requirements
* Linux
* Python 3.9+
* Docker
* Docker compose

### Local Auction run (for development):

* Terminal 1
```
git clone https://github.com/AtLeisureTime/auction.git
cd auction/

python3 -m venv my_env
source my_env/bin/activate
pip install -r requirements.txt

set -a
source .live.env
set +a
export DJANGO_SETTINGS_MODULE=auction.settings.local

docker compose -f docker-compose.local.yaml up --build
..
docker compose -f docker-compose.local.yaml down -v
deactivate
```
* Terminal 2
```
source my_env/bin/activate
set -a
source .live.env
set +a
export DJANGO_SETTINGS_MODULE=auction.settings.local

python auction/manage.py makemigrations
python auction/manage.py migrate
python auction/manage.py createsuperuser
python auction/manage.py runserver --settings=auction.settings.local
..
deactivate
```
* Terminal 3
```
source my_env/bin/activate
set -a
source .live.env
set +a
export DJANGO_SETTINGS_MODULE=auction.settings.local
cd auction/
celery -A auction worker -l info
..
deactivate
```

### Production-like Auction run
```
git clone https://github.com/AtLeisureTime/auction.git
cd auction/
chmod o+w .prod/web-docker-entrypoint.sh

cd auction/
openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
-keyout ssl/auctn.key -out ssl/auctn.crt \
-subj '/CN=*.auction.com' \
-addext 'subjectAltName=DNS:*.auction.com'

cd /tmp
mkdir auction
sudo chmod o+w auction
```

<br />Change the line in /etc/hosts:
```127.0.0.1	localhost```
to
```127.0.0.1	localhost auction.com www.auction.com```

Fix self-signed cert error in your browser. E.g., Firefox instructions - https://aboutssl.org/how-to-fix-mozilla-pkix-self-signed-cert-error/

Finally,
```
docker compose -f docker-compose.prod.yaml up --build
..
docker compose -f docker-compose.prod.yaml down -v
```

### Demo data
Demo auction data are in **test_data/**. Run this line locally or in auction-web docker container to load data to the database:
```
python auction/manage.py loaddata test_data/auctn_data.json
```
Reattach images from test_data/ to lots loaded in the previous line.
