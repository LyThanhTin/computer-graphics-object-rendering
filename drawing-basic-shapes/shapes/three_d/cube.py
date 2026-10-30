import numpy as np
import OpenGL.GL as GL

from core.shape import Shape
from core.palette import create_face_colors, CYBER_BLUE_VIOLET
from pathlib import Path
from cglibs.texutil import write_checker

class Cube(Shape):
    def __init__(self, size=1.0, shading='phong'):
        super().__init__(shading)

        self.size = size
        self.vertices, self.normals = self._generate_mesh()
        self.texcoords = self._generate_texcoords()
        self.vertex_count = len(self.vertices)
        self.supports_texture = True
        
        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.setup()

        project_root = Path(__file__).resolve().parents[2]
        texture_path = project_root / "assets" / "checker.png"

        if not texture_path.exists():
            texture_path.parent.mkdir(parents=True, exist_ok=True)
            write_checker(str(texture_path))

        _, texture_manager = self.programs["texture"]
        texture_manager.setup_texture("texture1", str(texture_path))

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

    def _generate_texcoords(self):
        """UVs for a 4x3 cube-cross atlas, one continuous panorama over all faces."""
        s = self.size / 2.0
        # Face order follows _generate_mesh(): +Z, -Z, +X, -X, +Y, -Y.
        slots = [(1, 1), (3, 1), (2, 1), (0, 1), (1, 0), (1, 2)]
        result = []
        for face_index, (slot_x, slot_y) in enumerate(slots):
            face_vertices = self.vertices[face_index * 6:(face_index + 1) * 6]
            for x, y, z in face_vertices:
                if face_index == 0:       # +Z
                    u, v = (x + s) / self.size, (y + s) / self.size
                elif face_index == 1:     # -Z
                    u, v = (s - x) / self.size, (y + s) / self.size
                elif face_index == 2:     # +X
                    u, v = (s - z) / self.size, (y + s) / self.size
                elif face_index == 3:     # -X
                    u, v = (z + s) / self.size, (y + s) / self.size
                elif face_index == 4:     # +Y
                    u, v = (x + s) / self.size, (s - z) / self.size
                else:                     # -Y
                    u, v = (x + s) / self.size, (z + s) / self.size
                # OpenGL texture coordinates have their origin at bottom-left.
                result.append(((slot_x + u) / 4.0, (2 - slot_y + v) / 3.0))
        return np.asarray(result, dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,    ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(3, self.texcoords, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()