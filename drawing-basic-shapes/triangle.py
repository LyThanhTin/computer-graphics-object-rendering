import os
import sys

import OpenGL.GL as GL
import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from shape import Shape

class Triangle(Shape):

    def __init__(self, shading='phong'):
        super().__init__(shading)

        self.vertices = np.array([
            [-0.5, -0.5, 0.0],
            [ 0.5, -0.5, 0.0],
            [ 0.0,  0.5, 0.0],
        ], dtype=np.float32)

        self.colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)

        self.normals = np.array([
            [ 0.4,  0.0, 1.0],
            [-0.3,  0.3, 1.0],
            [ 0.0, -0.4, 1.0],
        ], dtype=np.float32)

        self.normals /= np.linalg.norm(
            self.normals,
            axis=1,
            keepdims=True
        )

        self.vertex_count = 3

        self.setup()

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()