### Prerequisites
- docker
- docker-compose

### Installing

- add the discord token to a file called `discord.tk`, placed in root folder

- Production:
    1. Build the app `docker-compose -d --build`
    - Stop the application with `docker-compose down`

- Development:
    1. Build the app `docker-compose -f docker-compose.dev.yaml up -d --build`
    - Stop the application with `docker-compose -f docker-compose.dev.yaml down`


### Where is the persistant data located outside docker?
  - `sudo docker volume inspect lotr-triviabot_lotr-triviabot-storage`
      - prints an object, look for Mountpoint value, e.g. `... "Mountpoint": "/var/lib/docker/volumes/lotr-triviabot_lotr-triviabot-storage/_data" ...`

### Useful commands
- Starting the application
  - `docker-compose up -d`

- Stopping the application
  - `docker-compose down`


- Show logs
  - `docker logs lotr-triviabot --follow`

- Clean up docker cache/containers..
  - `docker system prune -a`

- Show volumes
  - `sudo docker volume ls`
