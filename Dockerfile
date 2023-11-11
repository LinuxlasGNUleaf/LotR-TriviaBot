FROM python:3.9

WORKDIR /app

# install requirements
ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# copy source code
COPY src .
ADD assets assets
ADD config config

# copy token files
RUN mkdir -p tokens
COPY discord.tk tokens/

# run bot
CMD ["python", "main.py"]