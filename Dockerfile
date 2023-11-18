FROM python:3.10-alpine

WORKDIR /app

# install requirements
ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# copy source code
ADD main.py main.py
ADD src src
ADD assets assets
ADD config config


# run bot
CMD ["python", "main.py"]