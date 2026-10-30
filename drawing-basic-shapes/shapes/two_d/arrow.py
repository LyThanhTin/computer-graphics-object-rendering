import numpy as np
import OpenGL.GL as GL

from cglibs import transform as T
from core.shape import Shape


class Arrow(Shape):
    def __init__(self, length=1.0, shaft_width=0.25, head_width=0.55, head_length=0.35, shading='phong'):
        super().__init__(shading)

        self.length = length
        self.shaft_width = shaft_width
        self.head_width = head_width
        self.head_length = head_length
        self.vertices = self._generate_vertices()
        self.vertex_count = 9

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
        L = self.length
        sw = self.shaft_width / 2
        hw = self.head_width / 2
        hl = self.head_length

        # 2D arrow pointing to the right
        p0 = np.array([-L / 2, -sw, 0.0])
        p1 = np.array([ L / 2 - hl, -sw, 0.0])
        p2 = np.array([ L / 2 - hl, -hw, 0.0])
        p3 = np.array([ L / 2,      0.0, 0.0])
        p4 = np.array([ L / 2 - hl,  hw, 0.0])
        p5 = np.array([ L / 2 - hl,  sw, 0.0])
        p6 = np.array([-L / 2,       sw, 0.0])

        return np.array([
            p0, p1, p5,
            p1, p2, p5,
            p2, p3, p4,
        ], dtype=np.float32)

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()
        self.enable_checker_texture(self.planar_texcoords(self.vertices, axes=(0, 1)))