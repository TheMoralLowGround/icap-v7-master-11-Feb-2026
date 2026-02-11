# Input Channel

### Installation Instructions

1. Clone this repository
2. Create .env file by copying .env.example file. Read insunctions inside it to set variables.
3. Start containers (start project). (execute in git bash for windows users)

```
./start.sh
```

4. Run Database migrations by running this command in another terminal (cd into current project folder first)

```
docker compose exec web python3 manage.py migrate
```

5. (Optional step) Create admin user by running this command in another terminal (cd into current project folder first)

```
docker compose exec web python3 manage.py createsuperuser
```

6. Stop containers (stop project). (execute in git bash for windows users)

```
./stop.sh
```

### Update Instructions

1. Push changes to this repository
2. Execute deploy script. (execute in git bash for windows users)

```
./deploy.sh
```

Above script will pull latest code from repositoty, build images and run containers again, migrate database changes and collect static files.

### Build Production Images (UBI Version) Without docker compose

```
docker build . -f Dockerfile -t input_channel_v7_web
docker build ./postgres -f ./postgres/Dockerfile -t input_channel_v7_postgres
```


### Developer Notes

Run commands inside python (web) container

```
docker compose exec web python3 manage.py createsuperuser
docker compose exec web python3 manage.py makemigrations
docker compose exec web python3 manage.py migrate
docker compose exec web python3 manage.py collectstatic --no-input --clear
```