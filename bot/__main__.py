from os import getenv
from pathlib import Path
import asyncio
from loguru import logger
from dotenv import load_dotenv

from bot import bot

load_dotenv()


@logger.catch
def start_bot():
    if token := getenv("DISCORD_TOKEN"):
        bot.run(token)
    else:
        raise Exception("You must set the DISCORD_TOKEN environment variable.")


@logger.catch
async def load_extensions():
    for path in Path("bot/extensions").glob("*.py"):
        filename = path.stem

        logger.info(f"Loading extension: {filename}")

        await bot.load_extension(f"bot.extensions.{filename}")

        logger.info(f"Loaded extension: {filename}")


if __name__ == "__main__":
    logger.info("Loading extensions")
    asyncio.run(load_extensions())

    logger.info("Starting bot")
    start_bot()