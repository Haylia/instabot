import requests
import instaloader
from pathlib import Path
from discord import File
from bot.utils.compression import compressfile
import os
from loguru import logger
from bot import bot
from dotenv import load_dotenv
load_dotenv()
instaloader_class = instaloader.Instaloader()

@logger.catch
def get_real_instagram_url(share_url):
    try:
        share_url = share_url.split("?igsh")[0]
        response = requests.get(share_url, allow_redirects=True)
        return response.url  # This is the real post URL
    except Exception:
        return share_url

@logger.catch
async def handle_instagram_link(post_url, user, ctx, error_func):
    channel_id = ctx.channel.id
    file_name = ""
    compressed_filename = False
    try:
        logger.info(f"Getting link {post_url}")
        post = instaloader.Post.from_shortcode(
            instaloader_class.context, post_url.split("/")[4]
        )
        is_video = False
        if "/reel/" in post_url or "/reels/" in post_url:
            is_video = True
            post_url = post.video_url
            file_name = instaloader_class.format_filename(
                post, target=post.owner_username
            )
        elif "/p/" in post_url:
            file_name = post.shortcode
            post_url = post.url
        file = requests.get(post_url)
        if file.status_code == 200:
            file_extension = "mp4" if is_video else "jpg"
            file_name = file_name + "." + file_extension
            with open(file_name, "wb") as f:
                f.write(file.content)
            compressed_filename = False
            if is_video and os.path.getsize(file_name) > 8 * 1024 * 1024:
                compressed_filename = f"compressed_{file_name}"
                compressfile(file_name, compressed_filename)

            await ctx.send(
                file=File(
                    f"{compressed_filename if compressed_filename else file_name}",
                    description=f"Posted by {user.id}",
                )
            )
            Path.unlink(f"{file_name}")
            if compressed_filename:
                Path.unlink(f"{compressed_filename}")
            return True
        else:
            await ctx.send(f"Failed to download image {post_url}")
    except (Exception, RuntimeError) as e:
        if e.message and e.message == "Session is closed":
            channel = bot.get_partial_messageable(channel_id)
            if channel:
                try:
                    await channel.send(
                        file=File(
                            f"{compressed_filename if compressed_filename else file_name}",
                            description=f"Posted by {user.id}",
                        )
                    )
                    return True
                except (Exception, RuntimeError) as e2:
                    logger.warning(f"instagram.py threw the following error: {e2}")
                    await error_func(post_url, user, ctx)
        logger.warning(f"instagram.py threw the following error: {e}")
        await error_func(post_url, user, ctx)

url_list = ["www.instagram.com", "instagram.com"]


def url_handler(url, user, ctx, error_func):
    url = get_real_instagram_url(url)
    return handle_instagram_link(url, user, ctx, error_func)
