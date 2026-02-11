FROM node:16.13.0

WORKDIR /app

COPY package*.json /app/

RUN npm install

COPY . .

EXPOSE 8080

CMD [ "npm", "run", "serve" ]