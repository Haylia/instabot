from discord.ext import commands
from bot import guild_ids
from bot import InstaBot
from os import getenv
from dotenv import load_dotenv, set_key
from loguru import logger

load_dotenv()


class Init(commands.Cog):
    def __init__(self, bot: InstaBot) -> None:
        self.bot = bot

    @commands.command(name="init", pass_context=True, guild_ids=guild_ids)
    async def _init(self, ctx):
        if users := getenv("DM_USERS"):
            user_list = users.split(", ")
            if ctx.author and ctx.author.id:
                logger.info(f"User id of {ctx.author.id}")
                user_id = str(ctx.author.id)
                if user_id not in user_list:
                    users = f"{users}, {ctx.author.id}"
                    set_key(".env", "DM_USERS", users)
                    await ctx.send(f"Added <@{user_id}> to the list")
                else:
                    await ctx.send("You are already in the list")
            else:
                await ctx.send(
                    "Couldn't get user who ran command, unsure how this happened."
                )
        else:
            await ctx.send("DM_USERS does not exist, this is a big oopsie.")


async def setup(bot):
    await bot.add_cog(Init(bot))
