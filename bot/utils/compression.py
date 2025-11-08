import subprocess
import os
from math import floor
from pathlib import Path
import shutil
from loguru import logger

def compressfile(input_file, output_file, target_mb=8, audio_quality=128):
    # compress a file to be under target_size in bytes (target_size in KB)
    # ensure we operate on absolute paths and place the output next to the input
    input_path = os.path.abspath(input_file)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # place output in the same directory as the input unless an absolute path is provided
    out_basename = os.path.basename(output_file)
    out_dir = os.path.dirname(output_file) if os.path.isabs(output_file) and os.path.dirname(output_file) else os.path.dirname(input_path) or os.getcwd()
    output_path = os.path.join(out_dir, out_basename)

    # ensure output has an extension (use same as input if missing)
    if not os.path.splitext(output_path)[1]:
        output_path += os.path.splitext(input_path)[1]

    length = _get_length(input_file)
    logger.info(f"Compressed video has length {length}")
    # ffmpeg: overwrite (-y) and set target video bitrate (in kb)

    bitrate = str(int(target_mb * 1024 * 8 / length))

    # First pass
    logger.info(input_file)
    subprocess.run([
        "ffmpeg",
        "-y",                # overwrite output
        "-i", input_file,
        "-c:v", "libx264",
        "-b:v", f"{bitrate}k",
        "-pass", "1",
        "-an",               # no audio for first pass
        "-f", "mp4",
        "/dev/null" if subprocess.os.name != "nt" else "NUL"
    ], check=True)

    # Second pass
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-c:v", "libx264",
        "-b:v", f"{bitrate}k",
        "-pass", "2",
        "-c:a", "aac",
        "-b:a", f"{audio_quality}k",
        output_file
    ], check=True)
    
    if os.path.getsize(output_file) > 8 * 1024 * 1024:
        logger.info(f"Failed with {target_mb}mb target, attempting {floor(0.75 * target_mb)} target")
        compressfile(output_file, f"a_{output_file}", floor(0.75 * target_mb), floor(audio_quality))
        Path.unlink(output_file)
        shutil.move(Path(f"a_{output_file}"), Path(output_file))
    return output_path

def _get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)