from os import getenv
from dotenv import load_dotenv
from discord import Intents, Game
from discord.ext import commands
from loguru import logger

load_dotenv()


class InstaBot(commands.Bot):
    async def on_ready(self):
        logger.info(f"Logged in as {self.user} on {len(self.guilds)} guilds.")
        logger.info(f"The bot prefix is {self.command_prefix}")


bot = InstaBot(
    command_prefix=[str(getenv("DISCORD_PREFIX"))],
    intents=Intents.all(),
    activity=Game(name="meme after meme after meme after meme"),
)

guild_ids = getenv("DISCORD_GUILDS").split(", ")
