from discord.ext import commands
from bot import guild_ids
from bot import InstaBot


class Test(commands.Cog):
    def __init__(self, bot: InstaBot) -> None:
        self.bot = bot
    @commands.command(
        name="test",
        pass_context=True,
        guild_ids=guild_ids
    )
    async def _test(self, ctx):
        await ctx.send("Response!")

async def setup(bot):
    await bot.add_cog(Test(bot))