import numpy as np
import OpenGL.GL as GL

from core.shape import Shape
from core.palette import create_gradient_colors, CYBER_CYAN_VIOLET

class Torus(Shape):
    def __init__(self, major_radius=0.6, minor_radius=0.2, major_segments=32, minor_segments=16, shading='phong'):
        super().__init__(shading)

        self.major_radius = major_radius
        self.minor_radius = minor_radius
        self.major_segments = major_segments
        self.minor_segments = minor_segments

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

        R = self.major_radius
        r = self.minor_radius

        for i in range(self.major_segments):
            u1 = 2.0 * np.pi * i / self.major_segments
            u2 = 2.0 * np.pi * (i + 1) / self.major_segments

            for j in range(self.minor_segments):
                v1 = 2.0 * np.pi * j / self.minor_segments
                v2 = 2.0 * np.pi * (j + 1) / self.minor_segments

                p1, n1 = self._point_and_normal(u1, v1, R, r)
                p2, n2 = self._point_and_normal(u2, v1, R, r)
                p3, n3 = self._point_and_normal(u2, v2, R, r)
                p4, n4 = self._point_and_normal(u1, v2, R, r)

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

    def _point_and_normal(self, u, v, R, r):
        # Position
        x = (R + r * np.cos(v)) * np.cos(u)
        y = r * np.sin(v)
        z = (R + r * np.cos(v)) * np.sin(u)

        # Normal
        nx = np.cos(v) * np.cos(u)
        ny = np.sin(v)
        nz = np.cos(v) * np.sin(u)

        normal = np.array([nx, ny, nz], dtype=np.float32)
        normal /= np.linalg.norm(normal)

        return [x, y, z], normal

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()
        self.enable_checker_texture(self.planar_texcoords(self.vertices, axes=(0, 2)))