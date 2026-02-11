# Frontend

### Installation Instructions
1. Clone this repository
2. Create .env file by copying .env.example file. Read insunctions inside it to set variables.
3. Start containers (start project). (execute in git bash for windows users)
```
./start.sh
```

5. Stop containers (stop project). (execute in git bash for windows users)
```
./stop.sh
```

### Update Instructions
1. Push changes to this repository
2. Execute deploy script. (execute in git bash for windows users)
```
./deploy.sh
```
Above script will pull latest code from repositoty, build images and run containers again.

### Build Production Images (Ubuntu Version) Without docker compose
```
docker build . -f Dockerfile.prod -t platform_frontend_server
```

### Build Production Images (UBI Version) Without docker compose
```
docker build . -f Dockerfile.ubi.prod -t platform_frontend_server
```

### Developer Notes
Run commands inside docker contanier
```
docker compose exec server npm install axios
docker compose exec server npm run build
```

### Auto Formatting Instructions
1. Open the frontend folder in vscode folder, (not other parent folder)
2. Install node 16.13.0 in remote/local machine
```
sudo apt-get install curl
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
command -v nvm
nvm install 16.13.0
nvm use 16.13.0
npm --version
```
3. Run npm install (to install packages locally)
4. Install Eslint pluggin (in vscode) in relevent remote/local environment
5. Upon saving of file, formatting should work, no need to start project to check auto-formatting