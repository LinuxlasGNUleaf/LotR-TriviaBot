### Prerequisites

- Production:
    - docker
    - docker-compose

### Installing

- add the discord token to a file called `discord.tk`, placed in root folder

- Production:
    1. Build the app `docker-compose -d --build`

### Useful commands
- Starting the application
  - `docker-compose up -d`

- Stopping the application
  - `docker-compose down`

- Show logs
  - `docker logs lotr-triviabot`

- Clean up docker cache/containers..
  - `docker system prune -a`
