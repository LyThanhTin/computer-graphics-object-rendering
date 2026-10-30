import numpy as np
import OpenGL.GL as GL

from core.shape import Shape

class Trapezoid(Shape):
    def __init__(self, top_width=0.6, bottom_width=1.0, height=0.8, shading='phong'):
        super().__init__(shading)

        self.top_width = top_width
        self.bottom_width = bottom_width
        self.height = height
        self.vertices = self._generate_vertices()
        self.vertex_count = 6

        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.normals = np.tile(
            np.array([[0.0, 0.0, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.setup()

    def _generate_vertices(self):
        top = self.top_width / 2
        bottom = self.bottom_width / 2
        h = self.height / 2

        return np.array([
            [-bottom, -h, 0.0],
            [ bottom, -h, 0.0],
            [ top,     h, 0.0],

            [-bottom, -h, 0.0],
            [ top,     h, 0.0],
            [-top,     h, 0.0],
        ], dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()
        self.enable_checker_texture(self.planar_texcoords(self.vertices, axes=(0, 1)))