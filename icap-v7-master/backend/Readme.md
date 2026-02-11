# Backend

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

5. Create admin user by running this command in another terminal (cd into current project folder first)

```
docker compose exec web python3 manage.py createsuperuser
```

6. Login into Django admin at localhost:8000/admin

   - In Django admin, Create a new definition setting record with the value given in definition-settings.json file supplied with this document.

7. Stop containers (stop project). (execute in git bash for windows users)

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

### Build Production Images (Ubuntu Version) Without docker compose

```
docker build . -t platform_backend_web
docker build . -t platform_backend_daphne
docker build . -t platform_backend_worker
docker build . -t platform_backend_celery
docker build . -t platform_backend_celery_beat
docker build ./nginx --build-arg CONFIG_FILE=nginx.prod.conf.template -t platform_backend_nginx
docker build ./postgres -t platform_backend_postgres
docker build ./redis -t platform_backend_redis
docker build ./rabbitmq -t platform_backend_rabbitmq
```

### Build Production Images (UBI Version) Without docker compose

```
docker build . -f Dockerfile.ubi -t platform_backend_web
docker build . -f Dockerfile.ubi -t platform_backend_daphne
docker build . -f Dockerfile.ubi -t platform_backend_worker
docker build . -f Dockerfile.ubi -t platform_backend_celery
docker build . -f Dockerfile.ubi -t platform_backend_celery_beat
docker build ./nginx -f ./nginx/Dockerfile.ubi --build-arg CONFIG_FILE=nginx.prod.conf.template -t platform_backend_nginx
docker build ./postgres -f ./postgres/Dockerfile.ubi -t platform_backend_postgres
docker build ./redis -f ./redis/Dockerfile.ubi -t platform_backend_redis
docker build ./rabbitmq -f ./rabbitmq/Dockerfile.ubi -t platform_backend_rabbitmq
```

### Data Import-Export

1. Export data from system A using following command

```
docker compose exec web python3 export_data.py
```

2. Copy the media/exported_data.json to media folder of system B.
3. Upload the data using following command in system B.

```
docker compose exec web python3 import_data.py
```

### Data Deletion Using Scripts

#### Delete Batches

-- Use following commands to removes batches from system (Database).
This script removes batches from database conditionally if Batch is uploaded in processing (production) mode and modified before 5 days.

```
docker compose exec web python3 remove_batch.py
```

Note: Batches uploaded in training mode needs to be deleted manually. those are not affected by the above script.

#### Delete Batch Status records

-- Use following commands to removes batch status records from system (Database). The removed batch status items will be saved to batch path in csv format.

- batch status records older than 5 days will be removed

```
docker compose exec web python3 remove_batch_status.py
```

- all batch status records will be deleted if above command is executed with argument "all"

```
docker compose exec web python3 remove_batch_status.py all
```

### Developer Notes

Run commands inside python (web) container

```
docker compose exec web python3 manage.py createsuperuser
docker compose exec web python3 manage.py makemigrations
docker compose exec web python3 manage.py migrate
docker compose exec web python3 manage.py collectstatic --no-input --clear
docker compose exec web python3 manage.py rqworker default
docker compose exec web daphne -b 0.0.0.0 -p 8001 app.asgi:application
docker compose exec web python3 manage.py shell
docker compose exec web python3 manage.py shell_plus --notebook
# docker compose exec web libreoffice --headless --convert-to xlsx Book1.xls
```
