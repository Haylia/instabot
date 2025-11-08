from discord.ext import commands
from bot import guild_ids
from bot import InstaBot


class Ping(commands.Cog):
    def __init__(self, bot: InstaBot) -> None:
        self.bot = bot
    @commands.command(
        name="ping", 
        pass_context=True,
        guild_ids=guild_ids
    )
    async def _ping(self, ctx):
        await ctx.send(f'{round(self.bot.latency * 1000)}ms')

async def setup(bot):
    await bot.add_cog(Ping(bot))