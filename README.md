# LotR Trivia Bot

A Discord bot with Lord of the Rings trivia, quotes, games, script lookup, and birthday reminders.

## Running locally

1. Use Python 3.10 or newer.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Put the Discord token in `$HOME/.config/discord/bots/lotr-bot/tokens/discord.tk`.
4. Start the bot with `python main.py`.

The bot creates its host-side state under `$HOME/.config/discord/bots/lotr-bot/`. Cache files are YAML so they can be inspected or edited directly. Existing `.cache` pickle files are migrated automatically the first time the bot starts after this update; the original files are kept as backups.

## Tests

Run the asset checks from the `tests` directory:

```bash
cd tests
python -m unittest discover -p '*_tests.py'
```

## TODO

- Add calendar reminders and automated calendar enrollment.
- Complete ban-roulette event and role management.
- Add trivia question submissions and review.