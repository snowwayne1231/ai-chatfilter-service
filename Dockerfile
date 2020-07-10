FROM node:current-slim

WORKDIR /usr/src/docker-django

RUN npm install

EXPOSE 8000
CMD [ "python", "manage.py", "runserver" ]

COPY . .