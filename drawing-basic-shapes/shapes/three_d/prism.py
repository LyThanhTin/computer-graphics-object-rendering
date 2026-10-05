import numpy as np
import OpenGL.GL as GL

from core.shape import Shape
from core.palette import create_gradient_colors, CYBER_VIOLET_PINK

class Prism(Shape):
    def __init__(self, sides=6, radius=0.5, height=1.0, shading='phong'):
        super().__init__(shading)

        if sides < 3:
            raise ValueError("Prism must have at least 3 sides")

        self.sides = sides
        self.radius = radius
        self.height = height

        self.vertices, self.normals = self._generate_mesh()
        self.vertex_count = len(self.vertices)

        """
        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )
        """
        self.colors = create_gradient_colors(
            self.vertex_count,
            CYBER_VIOLET_PINK
        )
        self.setup()

    def _generate_mesh(self):
        vertices = []
        normals = []

        bottom = []
        top = []

        # Generate bottom and top polygon vertices
        for i in range(self.sides):
            theta = 2 * np.pi * i / self.sides

            x = self.radius * np.cos(theta)
            y = self.radius * np.sin(theta)

            bottom.append([x, y, -self.height / 2])
            top.append([x, y, self.height / 2])

        # Side faces
        for i in range(self.sides):
            j = (i + 1) % self.sides

            p0 = np.array(bottom[i], dtype=np.float32)
            p1 = np.array(bottom[j], dtype=np.float32)
            p2 = np.array(top[j], dtype=np.float32)
            p3 = np.array(top[i], dtype=np.float32)

            normal = np.cross(p1 - p0, p3 - p0)
            normal = normal / np.linalg.norm(normal)

            # Two triangles per side
            vertices.extend([
                p0, p1, p2,
                p0, p2, p3
            ])

            normals.extend([
                normal, normal, normal,
                normal, normal, normal
            ])

        # Bottom face
        bottom_center = np.array(
            [0.0, 0.0, -self.height / 2],
            dtype=np.float32
        )

        bottom_normal = np.array(
            [0.0, 0.0, -1.0],
            dtype=np.float32
        )

        for i in range(self.sides):
            j = (i + 1) % self.sides

            vertices.extend([
                bottom_center,
                bottom[j],
                bottom[i]
            ])

            normals.extend([
                bottom_normal,
                bottom_normal,
                bottom_normal
            ])

        # Top face
        top_center = np.array(
            [0.0, 0.0, self.height / 2],
            dtype=np.float32
        )

        top_normal = np.array(
            [0.0, 0.0, 1.0],
            dtype=np.float32
        )

        for i in range(self.sides):
            j = (i + 1) % self.sides

            vertices.extend([
                top_center,
                top[i],
                top[j]
            ])

            normals.extend([
                top_normal,
                top_normal,
                top_normal
            ])

        return (
            np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32)
        )

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()