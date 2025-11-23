import yt_dlp
from pathlib import Path
from discord import File
from bot.utils.compression import compressfile
from bot import bot
import os
import shutil
from loguru import logger
import traceback

@logger.catch()
async def url_handler(url, user, ctx, error_func):
    channel_id = ctx.channel.id
    compressed = False
    filename = ""
    try:
        filename = get_uid_from_url(url)
        
        ydl_opts = {
            "format": "tbc below",
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4"
            }]
        }
        info = None
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        duration = info.get("duration")
        if duration is None:
            duration = 9999
        ydl_opts["format"] = f"bestvideo[height<={1080 if duration < 20 else 720 if duration < 40 else 480 if duration < 90 else 360 if duration < 600 else 240}][fps<=30][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error = ydl.download(url)
            if not error:
                current_filename = [name for name in os.listdir(Path(".")) if filename in name]
                if len(current_filename) == 0:
                    raise Exception("Download succeeded but no file found") 
                else:
                    current_filename = sorted(current_filename, key=lambda x: len(x), reverse=True)[0]
                filename = filename + ".mp4"
                if Path.exists(Path(filename)):
                    Path.unlink(Path(filename))
                shutil.move(Path(current_filename), Path(filename))
                if os.path.getsize(filename) > 8 * 1024 * 1024:
                    compressed = True
                    compressfile(filename, f"compressed_{filename}")

                await ctx.send(
                    file=File(
                        f"{'compressed_' if compressed else ''}{filename}",
                        description=f"Posted by {user.id}",
                    )
                )
                if Path.exists(Path(filename)):
                    Path.unlink(Path(filename))
                if Path.exists(Path(f"compressed_{filename}")):
                    Path.unlink(Path(f"compressed_{filename}"))
                return True
            else:
                raise Exception(error)
    except Exception as e:
        if hasattr(e, "message") and e.message == "Session is closed":
            channel = bot.get_partial_messageable(channel_id)
            if channel:
                try:
                    await channel.send(
                        file=File(
                            f"{'compressed_' if compressed else ''}{filename}",
                            description=f"Posted by {user.id}",
                        )
                    )
                    return True
                except (Exception, RuntimeError) as e2:
                    logger.warning(f"instagram.py threw the following error: {e2}")
                    await error_func(url, user, ctx)
        logger.warning(f"youtube.py threw the following error: {traceback.format_exc()}")
        if Path.exists(Path(filename)):
            Path.unlink(Path(filename))
        if Path.exists(Path(f"compressed_{filename}")):
            Path.unlink(Path(f"compressed_{filename}"))
        await error_func(url, user, ctx)

def get_uid_from_url(url: str):
    if "shorts" in url:
        return url.split("/shorts/")[1].split("?")[0]
    elif "youtu.be" in url:
        return url.split("/")[2].split("?")[0]
    else:
        return url.split("?v=")[1].split("?")[0].split("&")[0]

url_list = ["youtu.be", "youtube.com", "www.youtu.be", "www.youtube.com"]
