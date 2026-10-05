import numpy as np
import OpenGL.GL as GL

from core.shape import Shape
from core.palette import create_face_colors, CYBER_BLUE_VIOLET

class Cube(Shape):
    def __init__(self, size=1.0, shading='phong'):
        super().__init__(shading)

        self.size = size
        self.vertices, self.normals = self._generate_mesh()
        self.vertex_count = len(self.vertices)

        
        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )
        """
        self.colors = create_face_colors(
            face_count=6,
            vertices_per_face=6,
            palette=CYBER_BLUE_VIOLET
        )
        """
        self.setup()

    def _generate_mesh(self):
        s = self.size / 2.0

        faces = [
            # Front (+Z)
            (
                [[-s, -s, s],
                 [ s, -s, s],
                 [ s,  s, s],
                 [-s,  s, s]],
                [0, 0, 1]
            ),

            # Back (-Z)
            (
                [[ s, -s, -s],
                 [-s, -s, -s],
                 [-s,  s, -s],
                 [ s,  s, -s]],
                [0, 0, -1]
            ),

            # Right (+X)
            (
                [[s, -s, s],
                 [s, -s, -s],
                 [s, s, -s],
                 [s, s, s]],
                [1, 0, 0]
            ),

            # Left (-X)
            (
                [[-s, -s, -s],
                 [-s, -s, s],
                 [-s, s, s],
                 [-s, s, -s]],
                [-1, 0, 0]
            ),

            # Top (+Y)
            (
                [[-s, s, s],
                 [s, s, s],
                 [s, s, -s],
                 [-s, s, -s]],
                [0, 1, 0]
            ),

            # Bottom (-Y)
            (
                [[-s, -s, -s],
                 [s, -s, -s],
                 [s, -s, s],
                 [-s, -s, s]],
                [0, -1, 0]
            ),
        ]

        vertices = []
        normals = []

        for corners, normal in faces:
            vertices.extend([
                corners[0],
                corners[1],
                corners[2],

                corners[0],
                corners[2],
                corners[3],
            ])

            normals.extend([
                normal,
                normal,
                normal,
                
                normal,
                normal,
                normal,
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