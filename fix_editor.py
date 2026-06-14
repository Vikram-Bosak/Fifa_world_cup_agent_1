import sys

with open("editor/advanced_editor.py", "r") as f:
    content = f.read()

# Add ffprobe duration check before ffmpeg cmd
import_line = "import subprocess\n"
if "import subprocess" not in content:
    content = import_line + content

duration_logic = """
    duration = None
    try:
        duration_str = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
        ).decode().strip()
        if duration_str: duration = float(duration_str)
    except:
        pass

    cmd = ["ffmpeg", "-y", "-i", input_path, "-i", logo_path]
"""
content = content.replace('    cmd = ["ffmpeg", "-y", "-i", input_path, "-i", logo_path]', duration_logic)

# Replace -shortest with -t duration if duration exists
t_logic_long = """
    cmd.extend(["-map", "[outv]", "-map", "[outa]"])
    if duration:
        cmd.extend(["-t", str(duration)])
    else:
        cmd.extend(["-shortest"])
"""
content = content.replace('    cmd.extend(["-map", "[outv]", "-map", "[outa]", "-shortest"])', t_logic_long)

with open("editor/advanced_editor.py", "w") as f:
    f.write(content)
