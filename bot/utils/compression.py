import subprocess
from pathlib import Path, PurePath

def compressfile(input_file, output_file, target_size):
    # compress a file to be under target_size in bytes (target_size in KB)
    # ensure we operate on absolute paths and place the output next to the input
    input_path = Path.absolute(input_file)
    if not Path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # place output in the same directory as the input unless an absolute path is provided
    out_basename = Path.name(output_file)
    out_dir = PurePath.parent(output_file) if PurePath.is_absolute(output_file) and PurePath.parent(output_file) else PurePath.parent(input_path) or Path.cwd()
    output_path = PurePath(out_dir, out_basename)

    # ensure output has an extension (use same as input if missing)
    if not PurePath.suffix(output_path):
        output_path += PurePath.suffix(input_path)

    # ffmpeg: overwrite (-y) and set target video bitrate (in kb)
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-b:v", f"{target_size}k",
        output_path
    ]

    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        stderr = completed.stderr.decode(errors="ignore")
        raise RuntimeError(f"ffmpeg failed (rc={completed.returncode}): {stderr}")

    return output_path