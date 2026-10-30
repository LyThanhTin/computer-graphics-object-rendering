import numpy as np
import OpenGL.GL as GL

from cglibs import transform as T
from core.shape import Shape


class Ellipse(Shape):
    def __init__(self, rx=0.5, ry=0.3, segments=32, shading='phong'):
        super().__init__(shading)

        self.rx = rx
        self.ry = ry
        self.segments = segments
        self.vertices = self._generate_vertices()
        self.vertex_count = 3 * self.segments

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
        angles = np.linspace(0, 2 * np.pi, self.segments, endpoint=False)

        boundary = np.column_stack([
            self.rx * np.cos(angles),
            self.ry * np.sin(angles),
            np.zeros(self.segments)
        ]).astype(np.float32)

        center = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)

        vertices = []

        for i in range(self.segments):
            j = (i + 1) % self.segments
            vertices.extend([center[0], boundary[i], boundary[j]])

        return np.array(vertices, dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()
        self.enable_checker_texture(self.planar_texcoords(self.vertices, axes=(0, 1)))