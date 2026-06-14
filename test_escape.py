import subprocess
cmd = [
    "ffmpeg", "-f", "lavfi", "-i", "color=c=white:s=200x200",
    "-vf", "drawtext=text='ZLATAN\\'S FIFA DEBUT 🇸🇪🤩':fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':fontcolor=black:fontsize=50:x=50:y=50",
    "-frames:v", "1", "-y", "test_out.jpg"
]
subprocess.run(cmd, check=True)
