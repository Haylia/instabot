from discord import Embed, Color
from discord.ext import commands
from bot import guild_ids
from bot import InstaBot
from os import getenv
from dotenv import load_dotenv
from loguru import logger
load_dotenv()

class DMCheck(commands.Cog):
    def __init__(self, bot: InstaBot) -> None:
        self.bot = bot
    @commands.command(
        name="dmcheck", 
        pass_context=True,
        guild_ids=guild_ids
    )
    async def _dmcheck(self, ctx):
        if users := getenv("DM_USERS"):
            users = users.split(", ")
            user_message_count = {}
            for i in range(len(users)):
                logger.info(f"Getting user {users[i]}")
                if user := self.bot.get_user(int(users[i])):
                    try:
                        if not user.dm_channel:
                            await user.create_dm()
                        messages = 0
                        async for message in user.dm_channel.history(oldest_first=False):
                            if message.author == self.bot.user:
                                break
                            else:
                                messages += 1
                        user_message_count[user] = messages
                    except Exception:
                        await ctx.send(content=f"Could not open <@{users[i]}>'s dms.", allowed_mentions=[])
                        continue
                else:
                    await ctx.send(content=f"Failed to grab user <@{users[i]}>", allowed_mentions=[])
            user_message_count = dict(sorted(user_message_count.items(), key = lambda x: x[1], reverse=True))
            embed = Embed(title="DM Check", color=Color.blue())
            for user, messages in user_message_count.items():
                if messages:
                    embed.add_field(name=user.display_name, value=messages, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No users to check, therefore ending. Remember to onboard with the init command.")

async def setup(bot):
    await bot.add_cog(DMCheck(bot))