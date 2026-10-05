import numpy as np
import OpenGL.GL as GL
import glfw
import os

from cglibs.buffer import VAO
from cglibs import transform as T
from cglibs.shading import load_fgpi, handle_shading_key

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Shape:
    def __init__(self, shading='phong'):
        self.shading = shading
        self.model = T.identity()
        self.vao = VAO()
        self.programs = {}
        load_fgpi(self.programs, project_root)

    def setup_shaders(self):

        I_light = np.array([
            [0.9, 0.4, 0.6],
            [0.9, 0.4, 0.6],
            [0.9, 0.4, 0.6],
        ], dtype=np.float32)

        K_materials = np.array([
            [0.6, 0.4, 0.7],
            [0.6, 0.4, 0.7],
            [0.6, 0.4, 0.7],
        ], dtype=np.float32)

        light_pos = np.array(
            [0.0, 0.5, 0.9],
            dtype=np.float32
        )

        for name, (shader, uma) in self.programs.items():
            GL.glUseProgram(shader.render_idx)
            if name != 'interp':
                uma.upload_uniform_matrix3fv(I_light, 'I_light', False)
                uma.upload_uniform_matrix3fv(K_materials, 'K_materials', False)
                uma.upload_uniform_vector3fv(light_pos, 'light_pos')
                uma.upload_uniform_scalar1f(100.0, 'shininess')

    def draw(self, projection, view, model):
        shader, uma = self.programs[self.shading]
        GL.glUseProgram(shader.render_idx)

        # Model matrix of this object
        model_matrix = self.model

        # Camera view x object model
        modelView = view @ model_matrix

        uma.upload_uniform_matrix4fv(projection, 'projection', True)
        uma.upload_uniform_matrix4fv(modelView, 'modelview', True)

        self.vao.activate()
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertex_count)
        self.vao.deactivate()

    def key_handler(self, key):
        handle_shading_key(self, key)

        if key == glfw.KEY_R:
            self.reset_transform()
        elif key == glfw.KEY_UP:
            self.translate(0, 0.05)
        elif key == glfw.KEY_DOWN:
            self.translate(0, -0.05)
        elif key == glfw.KEY_LEFT:
            self.translate(-0.05, 0)
        elif key == glfw.KEY_RIGHT:
            self.translate(0.05, 0)
        elif key == glfw.KEY_EQUAL:
            self.scale(1.1)
        elif key == glfw.KEY_MINUS:
            self.scale(0.9)
        elif key == glfw.KEY_LEFT_BRACKET:
            self.rotate(angle=10)
        elif key == glfw.KEY_RIGHT_BRACKET:
            self.rotate(angle=-10)

    # -------------------------
    # Transformations
    # -------------------------

    def translate(self, x=0, y=0, z=0):
        self.model = self.model @ T.translate(x, y, z)

    def scale(self, x, y=None, z=None):
        self.model = self.model @ T.scale(x, y, z)

    def rotate(self, axis=(0, 0, 1), angle=0):
        self.model = self.model @ T.rotate(axis, angle)

    def reset_transform(self):
        self.model = T.identity()