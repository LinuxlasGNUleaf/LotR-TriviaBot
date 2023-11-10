FROM python:3.9

WORKDIR /app

COPY . .

RUN mkdir -p /root/.config/discord/bots/lotr-bot/tokens
COPY discord.tk /root/.config/discord/bots/lotr-bot/tokens/discord.tk

RUN pip install -r requirements.txt

CMD ["python", "main.py"]