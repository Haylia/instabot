import requests
import instaloader
from pathlib import Path
from discord import File
from bot.utils.compression import compressfile
import os
from loguru import logger

instaloader_class = instaloader.Instaloader()


def get_real_instagram_url(share_url):
    try:
        share_url = share_url.split("?igsh")[0]
        response = requests.get(share_url, allow_redirects=True)
        return response.url  # This is the real post URL
    except Exception as e:
        logger.error(f"Error fetching real Instagram URL: {e}")
        return share_url


async def handle_instagram_link(post_url, user, ctx):
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
    except Exception:
        await ctx.send(f"Error thrown when accessing {post_url}")


url_list = ["www.instagram.com", "instagram.com"]


def url_handler(url, user, ctx):
    url = get_real_instagram_url(url)
    return handle_instagram_link(url, user, ctx)
