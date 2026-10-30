import numpy as np
import OpenGL.GL as GL

from core.shape import Shape


class Mesh(Shape):
    def __init__(self, vertices, normals=None, colors=None, indices=None, texcoords=None, shading='phong'):
        super().__init__(shading)

        self.vertices = np.asarray(vertices, dtype=np.float32)

        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError("vertices must have shape (N, 3)")

        self.vertex_count = len(self.vertices)

        # Normals
        if normals is None:
            self.normals = self._compute_vertex_normals()
        else:
            self.normals = np.asarray(normals, dtype=np.float32)
            if self.normals.shape != self.vertices.shape:
                raise ValueError("normals must have the same shape as vertices")

        # Colors
        if colors is None:
            self.colors = np.tile(
                np.array([0.2, 0.7, 1.0], dtype=np.float32),
                (self.vertex_count, 1)
            )
        else:
            self.colors = np.asarray(colors, dtype=np.float32)
            if self.colors.shape != self.vertices.shape:
                raise ValueError("colors must have the same shape as vertices")

        # Texcoords
        self.texcoords = None

        if texcoords is not None:
            self.texcoords = np.asarray(texcoords, dtype=np.float32)

            if self.texcoords.shape != (self.vertex_count, 2):
                raise ValueError(
                    "texcoords must have shape (vertex_count, 2)"
                )

        # Indices
        self.indices = None

        if indices is not None:
            self.indices = np.asarray(indices, dtype=np.uint32).reshape(-1)
            
        # GPU buffers
        self.vao.add_vbo(0, self.vertices, ncomponents=3)
        self.vao.add_vbo(1, self.colors, ncomponents=3)
        self.vao.add_vbo(2, self.normals, ncomponents=3)
        if self.texcoords is None:
            # Imported OBJ/PLY meshes without UVs use a planar projection.
            self.texcoords = self.planar_texcoords(self.vertices, axes=(0, 1))
        self.vao.add_vbo(3, self.texcoords, ncomponents=2, dtype=GL.GL_FLOAT,
                         normalized=False, stride=0, offset=None)
        self.supports_texture = True
        if self.indices is not None:
            self.vao.add_ebo(self.indices)

        self.setup_shaders()
        from pathlib import Path
        from cglibs.texutil import write_checker
        texture_path = Path(__file__).resolve().parents[1] / "assets" / "checker.png"
        texture_path.parent.mkdir(parents=True, exist_ok=True)
        write_checker(str(texture_path))
        _, texture_manager = self.programs["texture"]
        texture_manager.setup_texture("texture1", str(texture_path))

    # Normal generation
    def _compute_vertex_normals(self):
        """
        Compute smooth vertex normals from triangle geometry.

        vertices are assumed to be arranged as triangles:
            [v0, v1, v2, v3, v4, v5, ...]
        """

        if len(self.vertices) % 3 != 0:
            raise ValueError(
                "Cannot compute normals automatically: "
                "vertices must contain complete triangles."
            )

        normals = np.zeros_like(self.vertices)

        for i in range(0, len(self.vertices), 3):
            a = self.vertices[i]
            b = self.vertices[i + 1]
            c = self.vertices[i + 2]

            normal = np.cross(b - a, c - a)

            length = np.linalg.norm(normal)

            if length > 1e-8:
                normal /= length

            normals[i] += normal
            normals[i + 1] += normal
            normals[i + 2] += normal

        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        lengths[lengths < 1e-8] = 1.0
        normals /= lengths

        return normals

    # Drawing
    def draw(self, projection, view, model):
        shader, uma = self.programs[self.shading]
        GL.glUseProgram(shader.render_idx)
        if self.shading == 'texture':
            for unit, texture in uma.textures.items():
                GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture['id'])
        modelView = view @ self.model
        uma.upload_uniform_matrix4fv(projection, 'projection', True)
        uma.upload_uniform_matrix4fv(modelView, 'modelview', True)

        self.vao.activate()

        if self.indices is not None:
            GL.glDrawElements(GL.GL_TRIANGLES, len(self.indices), GL.GL_UNSIGNED_INT, None)
        else:
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.vertex_count)

        self.vao.deactivate()