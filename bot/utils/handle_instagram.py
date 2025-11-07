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
        print(f"Error fetching real Instagram URL: {e}")
        return None

async def handle_instagram_link(ctx, post_url):
    try:
        post = instaloader.Post.from_shortcode(instaloader_class.context, post_url.split("/")[:-2])
        logger.info(f"{post_url.split("/")[:-2]}")
        logger.info(f"{post}")
        is_video = False
        if "/reel/" in post_url:
            is_video = True
            post_url = post.video_url
            file_name = instaloader_class.format_filename(post, target=post.owner_username)
        elif "/p/" in post_url:
            file_name = post.shortcode
            post_url = post.url
        file = instaloader_class.download_pic(filename=file_name, url=post_url, mtime=post.date_utc)
        if file:
            file_extension = "mp4" if is_video else "jpg"
            file_name = file_name + "." + file_extension
            if is_video and os.path.getsize(post.shortcode) > 8 * 1024 * 1024:
                compressed_filename = os.path.join(os.path.dirname(file_name) or ".", f"compressed_{file_name}")
                compressed_path = compressfile("file_name", compressed_filename, target_size=7000)  # target size in kb
            
            await ctx.send(file=File(f"{file_name if compressed_path is None else compressed_filename}", description=f"Posted by {ctx.author.id}"))
            Path.unlink("file_name")
            if compressed_filename is not None: 
                Path.unlink(f"{compressed_filename}")
            return True
        else:
            await ctx.send(f"Failed to download image {post_url}")
    except Exception:
        await ctx.send(f"Error thrown when accessing {post_url}")