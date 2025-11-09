from discord import Embed, Color
from urllib.parse import urlparse
from pathlib import Path
from loguru import logger
import importlib 

@logger.catch
def load_extensions():
    for path in Path("bot/utils/links/sites").glob("*.py"):
        filename = path.stem

        logger.info(f"Loading site handling for: {filename}")
        module = importlib.import_module(str(path).replace("\\", ".")[:-3])
        link_handler.add_domains(module.url_list, module.url_handler)
        logger.info(f"Loaded site handling for: {filename}")

class LinkHandler():
    def __init__(self):
        self.urls = dict()
    def add_domains(self, url_list, function: callable):
        for url in url_list:
            self.urls[url] = function
    async def _default_handling(self, url, user, ctx):
        embed = Embed(title="Site isn't handled", color=Color.blue())
        embed.add_field(name="User", value=user.display_name, inline=False)
        embed.add_field(name="Content", value=url, inline=False)
        await ctx.send(embed=embed)
        return True
    def handle_link(self, url, user, ctx):
        try:
            site = urlparse(url).netloc
            if site in self.urls.keys():
                return self.urls[site](url, user, ctx)
            else:
                return self._default_handling(url, user, ctx)
        except Exception:
            return self._default_handling(url, user, ctx)
   
link_handler = LinkHandler()
load_extensions()