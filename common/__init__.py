import os
import sys

# Ensure local ffmpeg binaries are available to subprocesses
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["PATH"] = project_root + os.pathsep + os.environ.get("PATH", "")
