import numpy as np
import OpenGL.GL as GL
import glfw
import os

from cglibs.buffer import VAO
from cglibs import transform as T
from cglibs.shading import load_shape_programs, handle_shading_key
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Shape:
    def __init__(self, shading='phong'):
        self.shading = shading
        self.model = T.identity()
        self.vao = VAO()
        self.programs = {}
        load_shape_programs(self.programs, project_root)
        self.supports_texture = False

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
            if name == "texture":
                uma.upload_uniform_scalar1f(0.3, "phong_factor")
    
    def _bind_active_texture(self):
        if self.shading != "texture":
            return

        _, uma = self.programs["texture"]

        for unit, texture in uma.textures.items():
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture["id"])


    @staticmethod
    def planar_texcoords(vertices, axes=(0, 1)):
        """Create normalized planar UVs for a triangle-expanded vertex array."""
        vertices = np.asarray(vertices, dtype=np.float32)
        coords = vertices[:, list(axes)]
        low = coords.min(axis=0)
        span = coords.max(axis=0) - low
        span[span < 1e-8] = 1.0
        return ((coords - low) / span).astype(np.float32)

    def enable_checker_texture(self, texcoords):
        """Attach UV coordinates and the project's default checker texture."""
        from pathlib import Path
        from cglibs.texutil import write_checker

        texcoords = np.asarray(texcoords, dtype=np.float32)
        if texcoords.shape != (self.vertex_count, 2):
            raise ValueError("Texture coordinates must have shape (vertex_count, 2)")

        # Avoid adding the UV attribute twice if a shape already has one.
        if 3 not in self.vao.vbo:
            self.vao.add_vbo(
                3, texcoords, ncomponents=2, dtype=GL.GL_FLOAT,
                normalized=False, stride=0, offset=None
            )
        self.texcoords = texcoords
        self.supports_texture = True

        texture_path = Path(project_root) / "assets" / "checker.png"
        texture_path.parent.mkdir(parents=True, exist_ok=True)
        write_checker(str(texture_path))
        _, texture_manager = self.programs["texture"]
        if not texture_manager.textures:
            texture_manager.setup_texture("texture1", str(texture_path))

    def set_texture(self, image_path):
        """Replace this shape's texture with a user-selected image file.

        Reuses texture unit 0 instead of allocating a new OpenGL texture every
        time the user chooses another image.
        """
        from cglibs.buffer import UManager

        if not self.supports_texture or "texture" not in self.programs:
            raise ValueError("The selected object does not support textures.")

        rgba = UManager.load_texture(str(image_path))
        # Cube textures are accepted as a single equirectangular panorama and
        # converted to a 4x3 cross atlas. Each face samples a different region,
        # so the image wraps around the whole cube instead of repeating per face.
        if self.__class__.__name__ == "Cube":
            rgba = self._equirectangular_to_cube_atlas(rgba)
        # OpenCV loads images top-to-bottom; flip rows for OpenGL UV convention.
        rgba = np.ascontiguousarray(np.flipud(rgba))
        _, manager = self.programs["texture"]
        if manager.textures:
            unit = min(manager.textures)
            texture_id = manager.textures[unit]["id"]
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA,
                            rgba.shape[1], rgba.shape[0], 0,
                            GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, rgba)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        else:
            # Normally the default checker texture is already registered.
            manager.setup_texture("texture1", str(image_path))
        self.texture_path = str(image_path)
        self.shading = "texture"

    @staticmethod
    def _equirectangular_to_cube_atlas(image):
        """Project a 2:1 panorama into a standard 4x3 cube cross atlas."""
        import cv2

        image = np.asarray(image, dtype=np.uint8)
        height, width = image.shape[:2]
        # A face resolution of half the panorama height is a good balance.
        tile = max(32, min(512, height // 2))
        atlas = np.zeros((tile * 3, tile * 4, 4), dtype=np.uint8)
        axis = (np.arange(tile, dtype=np.float32) + 0.5) / tile
        uu, vv = np.meshgrid(axis * 2.0 - 1.0, 1.0 - axis * 2.0)

        # Atlas positions are expressed in top-left image coordinates.
        faces = [
            # slot x, slot y, direction components
            (1, 1, lambda u, v: (u, v, np.ones_like(u))),       # +Z / front
            (3, 1, lambda u, v: (-u, v, -np.ones_like(u))),     # -Z / back
            (2, 1, lambda u, v: (np.ones_like(u), v, -u)),      # +X / right
            (0, 1, lambda u, v: (-np.ones_like(u), v, u)),      # -X / left
            (1, 0, lambda u, v: (u, np.ones_like(u), -v)),      # +Y / top
            (1, 2, lambda u, v: (u, -np.ones_like(u), v)),     # -Y / bottom
        ]

        for slot_x, slot_y, direction in faces:
            dx, dy, dz = direction(uu, vv)
            length = np.sqrt(dx * dx + dy * dy + dz * dz)
            dx, dy, dz = dx / length, dy / length, dz / length
            longitude = np.arctan2(dz, dx)
            latitude = np.arcsin(np.clip(dy, -1.0, 1.0))
            map_x = ((longitude / (2.0 * np.pi) + 0.5) * width).astype(np.float32)
            map_y = ((0.5 - latitude / np.pi) * height).astype(np.float32)
            map_x %= width
            map_y = np.clip(map_y, 0, height - 1)
            face = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_WRAP)
            y0, x0 = slot_y * tile, slot_x * tile
            atlas[y0:y0 + tile, x0:x0 + tile] = face
        return atlas

    def draw(self, projection, view, model):
        shader, uma = self.programs[self.shading]
        GL.glUseProgram(shader.render_idx)
        self._bind_active_texture()

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
        if key == glfw.KEY_T and not self.supports_texture:
            return
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

    # Transformations
    def translate(self, x=0, y=0, z=0):
        self.model = self.model @ T.translate(x, y, z)

    def scale(self, x, y=None, z=None):
        self.model = self.model @ T.scale(x, y, z)

    def rotate(self, axis=(0, 0, 1), angle=0):
        self.model = self.model @ T.rotate(axis, angle)

    def reset_transform(self):
        self.model = T.identity()