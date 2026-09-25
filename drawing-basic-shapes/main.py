import os
import sys
import glfw

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cglibs.viewer import Viewer, TrackballViewer
from triangle import Triangle
from polygon import Polygon
from rectangle import Rectangle
from trapezoid import Trapezoid
from ellipse import Ellipse
from circle import Circle
from star import Star
from arrow import Arrow


def main():
    viewer = Viewer(title="Assignment 1")
    testShape = Triangle()

    viewer.add(testShape)
    viewer.run()

if __name__ == "__main__":

    glfw.init()
    main()
    glfw.terminate()