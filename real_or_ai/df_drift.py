"""DepthFlow 'drone-like' camera: slow push-in + gentle lateral drift (looks like real footage).
Usage: python df_drift.py input -i frame.png main -o out.mp4 -w 1080 -h 960 -t 6 -f 30
"""
import sys, math, os
K = float(os.environ.get("DF_STRENGTH", "1.0"))
from attrs import define
from depthflow.scene import DepthScene

@define
class Drift(DepthScene):
    def update(self):
        e = 0.5 - 0.5 * math.cos(math.pi * self.tau)      # ease in/out
        self.state.height = (0.12 + 0.16 * e) * max(K, 0.5)               # depth strength (parallax) grows slowly
        self.state.offset = (0.22 * K * (e - 0.5), 0.04 * K * (e - 0.5))
        self.state.zoom = 1.0 - 0.06 * K * e                   # slow push-in
        self.state.isometric = 0.55
        self.state.steady = 0.25

if __name__ == "__main__":
    Drift().cli.meta(sys.argv[1:])
