import typing

import discord
from discord import app_commands

from src import utils
from src.DefaultCog import DefaultCog


class TriviaCog(DefaultCog):
    """
    handles the LotR-Trivia-Quiz integration for the bot, including profile / scoreboards
    """

    @app_commands.command(name='profile')
    @app_commands.describe(member='The user you want to fetch the')
    async def display_profile(self, interaction: discord.Interaction, member: typing.Optional[discord.Member]):
        """
        displays the user's profile (concerning the trivia minigame)
        """
        member = member if member is not None else interaction.user
        if member.id not in self.data['scores']:
            await interaction.response.send_message(
                f'{member.mention} hasn\'t played a game of trivia yet. To play, use `/trivia`!', ephemeral=True)
            return

        embed = discord.Embed(title=f'{utils.genitive(member.display_name)} profile')
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar)
        embed.colour = discord.Color.random()

        player_stats = self.data['scores'].get_row(member.id)
        self.logger.info(player_stats)

        embed.add_field(name=':abacus: Trivia games played:',
                        value=player_stats[0], inline=False)

        embed.add_field(name=':chart_with_upwards_trend: Percentage of games won:',
                        value=str(round((player_stats[1] / player_stats[0]) * 100, 1)) + '%', inline=False)

        embed.add_field(name=':dart: Current streak:',
                        value=player_stats[2], inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TriviaCog(bot))
