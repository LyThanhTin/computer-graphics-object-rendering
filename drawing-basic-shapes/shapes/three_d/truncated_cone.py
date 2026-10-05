import numpy as np
import OpenGL.GL as GL

from core.shape import Shape


class TruncatedCone(Shape):
    def __init__(self, bottom_radius=0.5, top_radius=0.3, height=1.0, segments=32, shading='phong'):
        super().__init__(shading)

        self.bottom_radius = bottom_radius
        self.top_radius = top_radius
        self.height = height
        self.segments = segments

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

        half_h = self.height / 2.0

        # Slope of side face
        slope = (self.bottom_radius - self.top_radius) / self.height

        # Side surface
        for i in range(self.segments):
            theta1 = 2.0 * np.pi * i / self.segments
            theta2 = 2.0 * np.pi * (i + 1) / self.segments

            c1, s1 = np.cos(theta1), np.sin(theta1)
            c2, s2 = np.cos(theta2), np.sin(theta2)

            bottom1 = [
                self.bottom_radius * c1,
                -half_h,
                self.bottom_radius * s1
            ]

            bottom2 = [
                self.bottom_radius * c2,
                -half_h,
                self.bottom_radius * s2
            ]

            top1 = [
                self.top_radius * c1,
                half_h,
                self.top_radius * s1
            ]

            top2 = [
                self.top_radius * c2,
                half_h,
                self.top_radius * s2
            ]

            # Surface normals
            n1 = np.array([c1, slope, s1], dtype=np.float32)
            n2 = np.array([c2, slope, s2], dtype=np.float32)

            n1 /= np.linalg.norm(n1)
            n2 /= np.linalg.norm(n2)

            # Triangle 1
            vertices.extend([bottom1, bottom2, top2])
            normals.extend([n1, n2,n2])

            # Triangle 2
            vertices.extend([bottom1, top2, top1])
            normals.extend([n1, n2, n1])

        # Bottom cap
        center_bottom = [0.0, -half_h, 0.0]

        for i in range(self.segments):
            theta1 = 2.0 * np.pi * i / self.segments
            theta2 = 2.0 * np.pi * (i + 1) / self.segments

            p1 = [
                self.bottom_radius * np.cos(theta1),
                -half_h,
                self.bottom_radius * np.sin(theta1)
            ]

            p2 = [
                self.bottom_radius * np.cos(theta2),
                -half_h,
                self.bottom_radius * np.sin(theta2)
            ]

            vertices.extend([center_bottom, p2, p1])
            normals.extend([
                [0.0, -1.0, 0.0],
                [0.0, -1.0, 0.0],
                [0.0, -1.0, 0.0]
            ])

        # Top cap
        center_top = [0.0, half_h, 0.0]

        for i in range(self.segments):
            theta1 = 2.0 * np.pi * i / self.segments
            theta2 = 2.0 * np.pi * (i + 1) / self.segments

            p1 = [
                self.top_radius * np.cos(theta1),
                half_h,
                self.top_radius * np.sin(theta1)
            ]

            p2 = [
                self.top_radius * np.cos(theta2),
                half_h,
                self.top_radius * np.sin(theta2)
            ]

            vertices.extend([center_top, p1, p2])
            normals.extend([
                [0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0]
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