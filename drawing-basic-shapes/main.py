import os
import sys
import glfw
import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cglibs.viewer import Viewer, TrackballViewer
from core.shape_factory import create_shape

def main():
    viewer = TrackballViewer(title="Assignment 1")
    viewer.shape_factory = create_shape
    viewer.run()

if __name__ == "__main__":
    glfw.init()
    main()
    glfw.terminate()