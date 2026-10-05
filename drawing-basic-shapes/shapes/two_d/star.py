import numpy as np
import OpenGL.GL as GL

from cglibs import transform as T
from core.shape import Shape


class Star(Shape):
    def __init__(self, outer_radius=0.5, inner_radius=0.2, points=5, shading='phong'):
        super().__init__(shading)

        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.points = points
        self.vertices = self._generate_vertices()
        self.vertex_count = 3 * (2 * self.points)

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
        vertices = []
        center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        total_vertices = 2 * self.points
        angles = np.linspace(0, 2 * np.pi, total_vertices, endpoint=False)
        boundary = []

        for i, angle in enumerate(angles):
            radius = (self.outer_radius if i % 2 == 0 else self.inner_radius)
            boundary.append([radius * np.cos(angle), radius * np.sin(angle), 0.0])

        boundary = np.array(boundary, dtype=np.float32)

        for i in range(total_vertices):
            j = (i + 1) % total_vertices
            vertices.extend([center, boundary[i], boundary[j]])

        return np.array(vertices, dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()