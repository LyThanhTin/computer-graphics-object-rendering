import numpy as np
import OpenGL.GL as GL

from core.shape import Shape
from pathlib import Path
from cglibs.texutil import write_checker

class Sphere(Shape):
    def __init__(self, radius=0.5, segments=32, rings=16, shading='phong'):
        super().__init__(shading)

        self.radius = radius
        self.segments = segments
        self.rings = rings

        self.vertices, self.normals, self.texcoords = self._generate_mesh()
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
        vertices = []
        normals = []
        texcoords = []

        for i in range(self.rings):
            phi1 = -np.pi / 2 + np.pi * i / self.rings
            phi2 = -np.pi / 2 + np.pi * (i + 1) / self.rings

            v1 = i / self.rings
            v2 = (i + 1) / self.rings

            for j in range(self.segments):
                theta1 = 2.0 * np.pi * j / self.segments
                theta2 = 2.0 * np.pi * (j + 1) / self.segments

                u1 = j / self.segments
                u2 = (j + 1) / self.segments

                p1 = self._point(phi1, theta1)
                p2 = self._point(phi1, theta2)
                p3 = self._point(phi2, theta2)
                p4 = self._point(phi2, theta1)

                n1 = np.array(p1, dtype=np.float32) / self.radius
                n2 = np.array(p2, dtype=np.float32) / self.radius
                n3 = np.array(p3, dtype=np.float32) / self.radius
                n4 = np.array(p4, dtype=np.float32) / self.radius

                # Triangle 1: p1, p2, p3
                vertices.extend([p1, p2, p3])
                normals.extend([n1, n2, n3])
                texcoords.extend([
                    [u1, v1],
                    [u2, v1],
                    [u2, v2],
                ])

                # Triangle 2: p1, p3, p4
                vertices.extend([p1, p3, p4])
                normals.extend([n1, n3, n4])
                texcoords.extend([
                    [u1, v1],
                    [u2, v2],
                    [u1, v2],
                ])

        return (
            np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32),
            np.array(texcoords, dtype=np.float32),
        )


    def _point(self, phi, theta):
        x = self.radius * np.cos(phi) * np.cos(theta)
        y = self.radius * np.sin(phi)
        z = self.radius * np.cos(phi) * np.sin(theta)

        return [x, y, z]

    def setup(self):
        self.vao.add_vbo(0, self.vertices,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,    ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(3, self.texcoords, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        
        self.setup_shaders()