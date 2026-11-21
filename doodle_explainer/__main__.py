import argparse
import os

from .engine import render_episode

p = argparse.ArgumentParser(description="Render a doodle-explainer Short from an episode JSON")
p.add_argument("episode", help="path to episode JSON (see doodle_explainer/episodes/)")
p.add_argument("-o", "--out", help="output mp4 (default: output/<episode>.mp4)")
p.add_argument("--preview", action="store_true", help="fast encode + print scene timings")
a = p.parse_args()
out = a.out or os.path.join("output", os.path.splitext(os.path.basename(a.episode))[0] + ".mp4")
render_episode(a.episode, out, preview=a.preview)
