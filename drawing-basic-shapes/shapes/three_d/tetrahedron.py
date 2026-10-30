import numpy as np
import OpenGL.GL as GL

from core.shape import Shape

class Tetrahedron(Shape):
    def __init__(self, size=1.0, shading='phong'):
        super().__init__(shading)

        self.size = size

        self.vertices, self.normals = self._generate_mesh()
        self.vertex_count = len(self.vertices)

        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.setup()

    def _generate_mesh(self):
        s = self.size

        # Four vertices of a regular tetrahedron
        p0 = np.array([ 1,  1,  1], dtype=np.float32) * s
        p1 = np.array([ 1, -1, -1], dtype=np.float32) * s
        p2 = np.array([-1, -1,  1], dtype=np.float32) * s
        p3 = np.array([-1,  1, -1], dtype=np.float32) * s

        faces = [
            (p0, p1, p2),
            (p0, p3, p1),
            (p0, p2, p3),
            (p1, p3, p2),
        ]

        vertices = []
        normals = []

        for a, b, c in faces:
            # Face normal
            normal = np.cross(c - a, b - a)
            normal /= np.linalg.norm(normal)

            vertices.extend([a, b, c])
            normals.extend([normal, normal, normal])

        return (
            np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32)
        )

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()
        self.enable_checker_texture(self.planar_texcoords(self.vertices, axes=(0, 1)))