import numpy as np
import OpenGL.GL as GL
import os

from cglibs import transform as T
from core.shape import Shape
from pathlib import Path
from cglibs.texutil import write_checker


class Rectangle(Shape):
    def __init__(self, width=1.0, height=1.0, shading='phong'):
        super().__init__(shading)

        self.width = width
        self.height = height
        self.vertices = self._generate_vertices()
        self.vertex_count = len(self.vertices)
        self.supports_texture = True

        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.normals = np.tile(
            np.array([[0.0, 0.0, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.texcoords = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],

            [0.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
        ], dtype=np.float32)

        self.setup()

    def _generate_vertices(self):
        w = self.width / 2
        h = self.height / 2

        return np.array([
            [-w, -h, 0.0],
            [ w, -h, 0.0],
            [ w,  h, 0.0],

            [-w, -h, 0.0],
            [ w,  h, 0.0],
            [-w,  h, 0.0],
        ], dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,    ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(3, self.texcoords, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        
        self.setup_shaders()

        project_root = Path(__file__).resolve().parents[2]
        texture_path = project_root / "assets" / "checker.png"

        write_checker(str(texture_path))

        _, texture_manager = self.programs["texture"]
        texture_manager.setup_texture("texture1", str(texture_path))