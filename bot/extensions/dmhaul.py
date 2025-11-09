from discord import User
from discord.ext import commands
from bot import guild_ids
from bot import InstaBot
from bot.links import link_handler
from loguru import logger
class DMHaul(commands.Cog):
    def __init__(self, bot: InstaBot) -> None:
        self.bot = bot
    @commands.command(
        name="dmhaul",
        pass_context=True,
        guild_ids=guild_ids
    )
    async def _dmhaul(self, ctx, user: User=None):
        if user is None:
            user = ctx.author
        if user.dm_channel is None: # always true fsr
            await user.create_dm()
        sent_any = False
        async with ctx.typing():
            messages = []
            async for message in user.dm_channel.history(oldest_first=False):
                if message.author == self.bot.user:
                    break
                else:
                    messages.append({"id": message.id, "content":message.content.strip()})
            logger.info(f"Sending {len(messages)} messages")
            for message in sorted(messages, key=lambda x: int(x["id"])):
                sent_any = await link_handler.handle_link(message["content"], user, ctx) or sent_any
        if sent_any:
            await user.dm_channel.send("Sent to here")        

async def setup(bot):
    await bot.add_cog(DMHaul(bot))


