"""Entertainment and Community commands for NoSpaceFGK."""

import random
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from decorators.command_dec import guild_only_command
from services.fun.meme_service import MemeService
from services.fun.joke_service import JokeService
from services.fun.gif_service import GifService
from services.fun.quote_service import QuoteService
from services.fun.fact_service import FactService
from services.fun.coinflip_service import CoinflipService
from services.fun.dice_service import DiceService
from services.fun.rps_service import RPSService
from services.fun.eightball_service import EightBallService
from repositories.fun_repository import FunRepository
from utils.embeds import success_embed, error_embed, info_embed
from utils.logger import logger

class FunCog(commands.Cog, name="Fun"):
    """Cog grouping all entertainment and community commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.memes: MemeService = bot.container.get(MemeService)
        self.jokes: JokeService = bot.container.get(JokeService)
        self.gifs: GifService = bot.container.get(GifService)
        self.quotes: QuoteService = bot.container.get(QuoteService)
        self.facts: FactService = bot.container.get(FactService)
        self.coinflip: CoinflipService = bot.container.get(CoinflipService)
        self.dice: DiceService = bot.container.get(DiceService)
        self.rps: RPSService = bot.container.get(RPSService)
        self.eightball: EightBallService = bot.container.get(EightBallService)
        self.repo: FunRepository = bot.container.get(FunRepository)
        logger.info("FunCog fully initialized.")

    @app_commands.command(name="meme", description="Display a random meme by category.")
    @app_commands.describe(category="Meme category: programming, wholesome, anime, gaming, science, space, general, technology.")
    async def meme(self, interaction: discord.Interaction, category: str = "general") -> None:
        await interaction.response.defer()
        try:
            m = await self.memes.get_meme(category)
            embed = success_embed(f"Meme: {m['title']}", f"Category: **{category}** | Subreddit: r/{m['subreddit']}")
            embed.set_image(url=m["url"])
            if m.get("post_link"):
                embed.url = m["post_link"]
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "meme")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Meme Error", str(e)))

    @app_commands.command(name="categories", description="List all available meme categories.")
    async def categories(self, interaction: discord.Interaction) -> None:
        cats = ["programming", "wholesome", "anime", "gaming", "science", "space", "general", "technology"]
        embed = info_embed("Meme Categories 📂", "\n".join(f"• `{c}`" for c in cats))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="joke", description="Tell a random joke.")
    @app_commands.describe(category="Joke category: programmer, dad, dark, general.")
    async def joke(self, interaction: discord.Interaction, category: str = "general") -> None:
        await interaction.response.defer()
        try:
            j = await self.jokes.get_joke(category)
            desc = j["setup"]
            if j.get("delivery"):
                desc += f"\n\n||{j['delivery']}||"
            embed = success_embed(f"Joke ({category.capitalize()}) 🎭", desc)
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "joke")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Joke Error", str(e)))

    @app_commands.command(name="gif", description="Display a reaction GIF.")
    @app_commands.describe(category="Category: happy, sad, angry, dance, facepalm, shrug.")
    async def gif(self, interaction: discord.Interaction, category: str) -> None:
        await interaction.response.defer()
        try:
            url = await self.gifs.get_reaction_gif(category)
            embed = success_embed(f"Reaction: {category.upper()} 🎬", "")
            embed.set_image(url=url)
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "gif")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("GIF Error", str(e)))

    @app_commands.command(name="quote", description="Get a random quote or showerthought.")
    @app_commands.describe(category="Category: motivation, showerthought, general.")
    async def quote(self, interaction: discord.Interaction, category: str = "general") -> None:
        await interaction.response.defer()
        try:
            q = await self.quotes.get_quote(category)
            author = q.get("author", "Unknown")
            embed = success_embed(f"Quote ({category.capitalize()}) 💬", f"\"{q['content']}\"\n\n— ***{author}***")
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "quote")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Quote Error", str(e)))

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="Your question to the 8-ball.")
    async def eightball(self, interaction: discord.Interaction, question: str) -> None:
        await interaction.response.defer()
        try:
            ans = await self.eightball.get_response()
            embed = success_embed("Magic 8-Ball 🎱", f"**Question:** *{question}*\n**Answer:** {ans}")
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "8ball")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("8ball Error", str(e)))

    @app_commands.command(name="coinflip", description="Flip a coin.")
    async def coinflip_cmd(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            res = await self.coinflip.flip()
            embed = success_embed("Coin Flip 🪙", f"The coin landed on: **{res}**!")
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "coinflip")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Coinflip Error", str(e)))

    @app_commands.command(name="dice", description="Roll a dice.")
    @app_commands.describe(sides="Number of sides on the dice (default: 6).")
    async def dice_cmd(self, interaction: discord.Interaction, sides: int = 6) -> None:
        await interaction.response.defer()
        try:
            res = await self.dice.roll(sides)
            embed = success_embed("Dice Roll 🎲", f"You rolled a d{sides} and got: **{res}**!")
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "dice")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Dice Error", str(e)))

    @app_commands.command(name="rps", description="Play Rock-Paper-Scissors against the bot.")
    @app_commands.describe(choice="Choose: rock, paper, or scissors.")
    async def rps_cmd(self, interaction: discord.Interaction, choice: str) -> None:
        await interaction.response.defer()
        try:
            res = await self.rps.play(choice)
            status_map = {
                "win": "Victory! You won! 🎉",
                "loss": "Defeat! I won! 🤖",
                "tie": "It is a tie! 🤝"
            }
            embed = success_embed("Rock Paper Scissors 🪨📄✂️", f"**Your Choice:** {res['user'].title()}\n**My Choice:** {res['bot'].title()}\n\n**Result:** {status_map[res['result']]}")
            await self.repo.log_fun_usage(interaction.guild_id, interaction.user.id, "rps")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("RPS Error", str(e)))

    @app_commands.command(name="choose", description="Randomly choose from a list of options.")
    @app_commands.describe(options="Comma separated list of options.")
    async def choose(self, interaction: discord.Interaction, options: str) -> None:
        opts = [o.strip() for o in options.split(",") if o.strip()]
        if len(opts) < 2:
            return await interaction.response.send_message(embed=error_embed("Choose Error", "Please provide at least 2 options separated by commas."), ephemeral=True)
        choice = random.choice(opts)
        await interaction.response.send_message(embed=success_embed("Random Choice 🧠", f"Out of your options, I choose:\n**{choice}**"))

    @app_commands.command(name="randomnumber", description="Generate a random number in range.")
    @app_commands.describe(min_val="Minimum value.", max_val="Maximum value.")
    async def randomnumber(self, interaction: discord.Interaction, min_val: int = 1, max_val: int = 100) -> None:
        if min_val >= max_val:
            return await interaction.response.send_message(embed=error_embed("Error", "Min value must be strictly less than Max value."), ephemeral=True)
        val = random.randint(min_val, max_val)
        await interaction.response.send_message(embed=success_embed("Random Number 🔢", f"Random number between `{min_val}` and `{max_val}`:\n**{val}**"))

    @app_commands.command(name="mock", description="mOcK a sPeCiFiC TeXt.")
    @app_commands.describe(text="Text to mock.")
    async def mock(self, interaction: discord.Interaction, text: str) -> None:
        mocked = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))
        await interaction.response.send_message(mocked)

    @app_commands.command(name="compliment", description="Send a nice compliment to someone.")
    @app_commands.describe(member="Member to compliment.")
    async def compliment(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        from tools.fun.compliment import COMPLIMENTS
        comp = random.choice(COMPLIMENTS)
        target = member.mention if member else interaction.user.mention
        await interaction.response.send_message(f"{target}, {comp}")

    @app_commands.command(name="roast", description="Roast someone.")
    @app_commands.describe(member="Member to roast.")
    async def roast(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        from tools.fun.roast import ROASTS
        rst = random.choice(ROASTS)
        target = member.mention if member else interaction.user.mention
        await interaction.response.send_message(f"{target}, {rst}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FunCog(bot))
