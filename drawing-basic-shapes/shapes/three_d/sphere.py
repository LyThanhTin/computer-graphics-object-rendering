import numpy as np
import OpenGL.GL as GL

from core.shape import Shape


class Sphere(Shape):
    def __init__(self, radius=0.5, segments=32, rings=16, shading='phong'):
        super().__init__(shading)

        self.radius = radius
        self.segments = segments
        self.rings = rings

        self.vertices, self.normals = self._generate_mesh()
        self.vertex_count = len(self.vertices)

        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.setup()

    def _generate_mesh(self):
        vertices = []
        normals = []

        # Latitude × longitude
        for i in range(self.rings):
            phi1 = -np.pi / 2 + np.pi * i / self.rings
            phi2 = -np.pi / 2 + np.pi * (i + 1) / self.rings

            for j in range(self.segments):
                theta1 = 2.0 * np.pi * j / self.segments
                theta2 = 2.0 * np.pi * (j + 1) / self.segments

                # Four points of one surface patch
                p1 = self._point(phi1, theta1)
                p2 = self._point(phi1, theta2)
                p3 = self._point(phi2, theta2)
                p4 = self._point(phi2, theta1)

                # Sphere normal = normalized position
                n1 = np.array(p1, dtype=np.float32) / self.radius
                n2 = np.array(p2, dtype=np.float32) / self.radius
                n3 = np.array(p3, dtype=np.float32) / self.radius
                n4 = np.array(p4, dtype=np.float32) / self.radius

                # Triangle 1
                vertices.extend([p1, p2, p3])
                normals.extend([n1, n2, n3])

                # Triangle 2
                vertices.extend([p1, p3, p4])
                normals.extend([n1, n3, n4])

        return (
            np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32)
        )

    def _point(self, phi, theta):
        x = self.radius * np.cos(phi) * np.cos(theta)
        y = self.radius * np.sin(phi)
        z = self.radius * np.cos(phi) * np.sin(theta)

        return [x, y, z]

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()