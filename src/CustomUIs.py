import asyncio
import random
import string

import discord
import pytz
from discord import ui

import src.utils as utils
from src.utils import create_embed, genitive


# =====> TRIVIA QUIZ UI
class TriviaQuizButton(ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, i: int, correct: bool):
        self.index = i
        self.correct = correct
        super().__init__(style=style, label=str(i + 1))

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.view.player.id:
            await interaction.response.defer()
            self.style = discord.ButtonStyle.green if self.correct else discord.ButtonStyle.red
            await self.view.finish_quiz(self.correct)
        elif interaction.user.id not in self.view.warned_users:
            self.view.warned_users.append(interaction.user.id)
            await interaction.response.send_message("You are not the user that started this quiz!", ephemeral=True)
        else:
            await interaction.response.defer()


class TriviaSelectButton(ui.Button['TriviaView']):
    def __init__(self, style: discord.ButtonStyle, title: str, continue_game: bool):
        self.continue_game = continue_game
        super().__init__(style=style, label=title, row=2)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.view.player.id:
            await interaction.response.defer()
            if self.continue_game:
                self.view.delete_all_buttons()
                self.view.setup_quiz()
            else:
                self.view.delete_all_buttons()
                await self.view.update_message()
                self.view.stop()
        elif interaction.user.id not in self.view.warned_users:
            self.view.warned_users.append(interaction.user.id)
            await interaction.followup.send_message("You are not the user that started this quiz!", ephemeral=True)
        else:
            await interaction.response.defer()


class TriviaView(ui.View):

    def __init__(self, interaction: discord.Interaction, cog):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.player: discord.Member = interaction.user
        self.cog = cog
        self.config: dict = cog.config['game']
        self.scoreboard: DataManager = cog.data['scores']

        self.trivia_msg = None
        self.trivia_embed = None
        self.trivia_note = None
        self.trivia_hint = None

        self.quiz_running = False
        self.quiz_counter = 0

        self.buttons = []
        self.warned_users = []
        self.correct_index = -1

        self.setup_quiz()

    def disable_all_buttons(self):
        for i, button in enumerate(self.buttons):
            button.disabled = True

    def delete_all_buttons(self):
        self.clear_items()
        self.buttons.clear()

    async def update_message(self):
        self.trivia_embed.set_field_at(len(self.trivia_embed.fields) - 1,
                                       name=self.trivia_embed.fields[-1].name,
                                       value=f'```\n{self.trivia_note if self.trivia_note else " "}```',
                                       inline=False)
        if self.trivia_hint:
            self.trivia_embed.set_footer(text=self.trivia_hint)
        else:
            self.trivia_embed.remove_footer()

        if self.trivia_msg is not None:
            await self.trivia_msg.edit(embed=self.trivia_embed, view=self)
        else:
            await self.interaction.response.send_message(embed=self.trivia_embed, view=self)
            self.trivia_msg = await self.interaction.original_response()

    async def on_timeout(self):
        self.disable_all_buttons()
        await self.update_message()

    def setup_quiz(self):
        if self.player.id not in self.scoreboard:
            self.scoreboard.add_row(self.player.id)
        played_games = self.scoreboard.get(self.player.id, 'played')
        played_games += 1
        self.scoreboard.set(self.player.id, 'played', played_games)
        self.quiz_counter += 1
        # send trivia embed
        self.trivia_embed, answer_count, self.correct_index, timeout = self.cog.get_trivia_question(self.player,
                                                                                                    played_games)

        # setup trivia question buttons
        self.delete_all_buttons()
        for i in range(answer_count):
            new_button = TriviaQuizButton(discord.ButtonStyle.blurple, i, i == self.correct_index)
            self.add_item(new_button)
            self.buttons.append(new_button)

        # run quiz
        self.cog.bot.loop.create_task(self.run_quiz(timeout))

    async def run_quiz(self, timeout):
        self.quiz_running = True
        self.timeout = None
        current_quiz = self.quiz_counter
        await self.update_message()
        await asyncio.sleep(timeout)
        if self.quiz_running and current_quiz == self.quiz_counter:
            await self.finish_quiz(False, timeout=True)

    async def finish_quiz(self, correct, timeout=False):
        if not self.quiz_running:
            return
        self.quiz_running = False

        # adjust win count of player accordingly
        if correct:
            self.scoreboard.add(self.player.id, 'streak', 1)
            # TODO: do earned points calc
            earned_points = self.scoreboard.get(self.player.id, 'streak')
            self.scoreboard.add(self.player.id, 'points', earned_points)
        else:
            self.scoreboard.set(self.player.id, 'streak', 0)

        self.trivia_note = self.cog.create_response(self.player, correct)
        if timeout:
            self.trivia_hint = "\nYou didn't answer in time!"
        elif random.uniform(0, 1) <= self.config['tip_probability']:
            self.trivia_hint = random.choice(self.config['tips']).format(self.config['link'])
        else:
            self.trivia_hint = None

        continue_button = TriviaSelectButton(discord.ButtonStyle.green, 'CONTINUE', True)
        stop_button = TriviaSelectButton(discord.ButtonStyle.red, 'STOP', False)

        # disable all quiz buttons
        self.disable_all_buttons()

        # add select buttons
        self.add_item(continue_button)
        self.add_item(stop_button)
        self.buttons.append(continue_button)
        self.buttons.append(stop_button)

        self.timeout = self.config['select_timeout']
        await self.update_message()


# =====> BIRTHDAY UI
class BirthdayRegistrationView(ui.View):
    def __init__(self, interaction: discord.Interaction, cog):
        super().__init__(timeout=cog.config['registration']['timeout'] * 60)
        self.msg = None
        self.cog = cog
        self.interaction: discord.Interaction = interaction
        self.button = BirthdayRegistrationButton(cog)
        self.add_item(self.button)

    async def run(self):
        self.msg = await self.interaction.response.send_message(
            self.cog.config['registration']['hint'],
            view=self)

    async def on_timeout(self):
        for element in self.children:
            element.disabled = True
        await self.msg.edit(view=self)


class BirthdayRegistrationButton(ui.Button):
    def __init__(self, cog):
        self.cog = cog
        super().__init__(label='Birthday Registration',
                         emoji=cog.config['registration']['unicode_emoji'])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BirthdayRegistrationModal(self.cog, interaction.user))


class BirthdayRegistrationModal(ui.Modal, title='Birthday Registration Form'):
    def __init__(self, cog, user: discord.User):
        super().__init__()
        self.cog = cog
        self.user = user
        if self.user.id in self.cog.data['dates']:
            self.old_entry = self.cog.data['dates'].get_row(user.id)
            name, month, day, tz, _ = self.old_entry
        else:
            self.old_entry = None
            name, month, day, tz = (user.name, 1, 1, 'UTC')

        self.components = [
            ui.TextInput(label='Name', min_length=1, max_length=32, default=name),
            ui.TextInput(label='Month:', min_length=1, max_length=2, default=month),
            ui.TextInput(label='Day of the Month:', min_length=1, max_length=2, default=day),
            ui.TextInput(label='Timezone:', min_length=1, max_length=100, default=tz)
        ]
        for component in self.components:
            self.add_item(component)

    async def on_submit(self, interaction: discord.Interaction):
        name: str
        month: str
        day: str
        tz: str
        name, month, day, tz = (x.value for x in self.components)

        valid, msg = utils.validate_date_str(month, day)
        if not valid:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        month: int = int(month)
        day: int = int(day)

        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message(
                'Timezone not valid. Choose a `TZ Identifier` from here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List',
                ephemeral=True)
            return

        self.cog.register_with_db(self.user.id, name, month, day, tz)

        embed = self.cog.create_birthday_embed(
            name=name,
            month=month,
            day=day,
            tz=pytz.timezone(tz),
            avatar=self.user.avatar
        )

        await interaction.response.send_message(
            f'__**{self.user.name}**__ {"updated" if self.old_entry else "registered"} their birthday:',
            embed=embed
        )


class HangmanButton(ui.Button['HangmanView']):
    def __init__(self, letter: str, correct: bool, row: int):
        self.letter = letter
        self.correct = correct
        super().__init__(style=discord.ButtonStyle.blurple, label=letter, row=row)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.view.player.id:
            await interaction.response.defer()
            self.style = discord.ButtonStyle.green if self.correct else discord.ButtonStyle.red
            self.disabled = True
            await self.view.register_letter(self.letter)
        elif interaction.user.id not in self.view.warned_users:
            self.view.warned_users.append(interaction.user.id)
            await interaction.response.send_message("You are not the user that started this quiz!", ephemeral=True)
        else:
            await interaction.response.defer()


class HangmanView(ui.View):
    def __init__(self, interaction: discord.Interaction, cog, word: str):
        super().__init__()
        self.interaction: discord.Interaction = interaction
        self.player: discord.Member = interaction.user
        self.cog = cog
        self.config: dict = cog.config['game']
        self.scoreboard: DataManager = cog.data['scores']

        self.word = word
        self.correct_letters: set = set(word.upper()).intersection(string.ascii_uppercase)
        self.guessed_letters: set = set()

        self.buttons: list = []
        self.warned_users: list = []

        self.hangman_msg: discord.Message = None
        self.hangman_embed: discord.Embed = None

        self.strikes: int = 0
        self.running: bool = False

        self.setup_hangman()

    def setup_hangman(self):
        self.running = True
        self.hangman_embed = create_embed(title=self.generate_hangman_string(),
                                          author_field=(f'{genitive(self.player.name)} game of Hangman', None,
                                                        self.player.avatar.url),
                                          content=f"```{self.config['game_states'][self.strikes]}```",
                                          footnote=self.config['footnote'])
        for i, letter in enumerate(self.config['buttons']):
            button = HangmanButton(letter, letter in self.correct_letters, i // 5)
            self.add_item(button)
            self.buttons.append(button)
        self.cog.bot.loop.create_task(self.run_hangman())

    def generate_hangman_string(self, uncover: bool = False) -> str:
        hangman_string = ""
        for letter in self.word:
            if letter.upper() in self.guessed_letters or uncover:
                hangman_string += f'__{letter}__ '
            elif letter.upper() in string.ascii_uppercase:
                hangman_string += '\_ '
            else:
                hangman_string += '  '
        return hangman_string.strip()

    async def run_hangman(self):
        await self.interaction.response.send_message(embed=self.hangman_embed, view=self)
        self.hangman_msg = await self.interaction.original_response()

    async def register_letter(self, letters: str):
        letters = [x for x in letters if x in string.ascii_uppercase]
        new_guessed_letter = False
        for letter in letters:
            if letter not in self.guessed_letters:
                self.guessed_letters.add(letter)
                if letter in self.correct_letters:
                    new_guessed_letter = True

        if not new_guessed_letter:
            self.strikes += 1

        if self.strikes >= len(self.config['game_states']):
            await self.finish_game(False)
            return
        if all([x in self.guessed_letters for x in self.correct_letters]):
            await self.finish_game(True)
            return

        self.hangman_embed.title = self.generate_hangman_string()
        self.hangman_embed.description = f"```{self.config['game_states'][self.strikes]}```"
        await self.hangman_msg.edit(embed=self.hangman_embed, view=self)

    async def finish_game(self, won: bool):
        self.hangman_embed.title = self.generate_hangman_string(uncover=True)
        state: str = self.config['game_won'] if won else self.config['game_over']
        footer: str = self.config['footnote_won'] if won else self.config['footnote_lost']
        self.hangman_embed.description = f"```{state}```"
        self.hangman_embed.set_footer(text=footer)
        for button in self.buttons:
            self.remove_item(button)
        await self.hangman_msg.edit(embed=self.hangman_embed, view=self)
        self.stop()
