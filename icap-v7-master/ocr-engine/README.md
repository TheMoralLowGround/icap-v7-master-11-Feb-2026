# OCR Engine (Internal)

### Installation Instructions
1. Clone this repository
2. Create .env file by copying .env.example file. Read insunctions inside it to set variables.
3. Start containers (start project). (execute in git bash for windows users)
```
./start.sh
```
4. Stop containers (stop project). (execute in git bash for windows users)
```
./stop.sh
```

### Update Instructions
1. Push changes to this repository
2. Execute deploy script. (execute in git bash for windows users)
```
./deploy.sh
```
Above script will pull latest code from repositoty, make docbuilder_docker file executable and build images and run containers again.

