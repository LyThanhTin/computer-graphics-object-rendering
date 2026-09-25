import numpy as np
import OpenGL.GL as GL

from shape import Shape


class Polygon(Shape):
    def __init__(self, n, radius=0.5, shading='phong'):
        super().__init__(shading)

        self.n = n
        self.radius = radius
        self.vertices = self._generate_vertices()
        self.vertex_count = len(self.vertices)

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
        angles = np.linspace(0, 2 * np.pi, self.n, endpoint=False)

        boundary = np.column_stack([
            self.radius * np.cos(angles),
            self.radius * np.sin(angles),
            np.zeros(self.n)
        ]).astype(np.float32)

        center = np.array([[0, 0, 0]], dtype=np.float32)

        vertices = []

        for i in range(self.n):
            j = (i + 1) % self.n

            vertices.extend([
                center[0],
                boundary[i],
                boundary[j]
            ])

        return np.array(vertices, dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()