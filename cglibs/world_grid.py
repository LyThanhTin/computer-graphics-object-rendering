"""Neon world-space grid and XYZ axis overlay for TrackballViewer."""
import numpy as np
import ctypes
import OpenGL.GL as GL

VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
uniform mat4 projection;
uniform mat4 modelview;
out vec3 v_color;
void main() {
    v_color = color;
    gl_Position = projection * modelview * vec4(position, 1.0);
}
"""
FRAGMENT_SHADER = """#version 330 core
in vec3 v_color;
out vec4 out_color;
void main() { out_color = vec4(v_color, 0.82); }
"""

class WorldGrid:
    def __init__(self, extent=10, step=1):
        self.visible = True
        positions, colors = [], []
        # A subtle floor grid on the XZ plane.
        for n in np.arange(-extent, extent + step, step):
            c = [0.12, 0.28, 0.36] if abs(n) > 1e-6 else [0.0, 0.92, 1.0]
            positions.extend([[-extent, -0.75, n], [extent, -0.75, n]])
            colors.extend([c, c])
            c = [0.12, 0.22, 0.34] if abs(n) > 1e-6 else [1.0, 0.18, 0.62]
            positions.extend([[n, -0.75, -extent], [n, -0.75, extent]])
            colors.extend([c, c])
        # World axes run through the origin and are drawn brighter than the grid.
        axis_len = extent
        for end, color in [([axis_len, 0, 0], [1.0, 0.18, 0.62]),
                           ([0, axis_len, 0], [0.0, 0.95, 1.0]),
                           ([0, 0, axis_len], [0.62, 0.30, 1.0])]:
            positions.extend([[0, 0, 0], end])
            colors.extend([color, color])
        self.count = len(positions)
        data = np.column_stack((np.asarray(positions, np.float32), np.asarray(colors, np.float32)))
        self.program = GL.glCreateProgram()
        shaders = []
        for kind, source in [(GL.GL_VERTEX_SHADER, VERTEX_SHADER), (GL.GL_FRAGMENT_SHADER, FRAGMENT_SHADER)]:
            shader = GL.glCreateShader(kind)
            GL.glShaderSource(shader, source)
            GL.glCompileShader(shader)
            if not GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS):
                raise RuntimeError(GL.glGetShaderInfoLog(shader).decode())
            GL.glAttachShader(self.program, shader)
            shaders.append(shader)
        GL.glLinkProgram(self.program)
        if not GL.glGetProgramiv(self.program, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.program).decode())
        for shader in shaders:
            GL.glDeleteShader(shader)
        self.vao = GL.glGenVertexArrays(1)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, data.nbytes, data, GL.GL_STATIC_DRAW)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, 24, ctypes.c_void_p(0))
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, False, 24, ctypes.c_void_p(12))
        GL.glEnableVertexAttribArray(1)
        GL.glBindVertexArray(0)

    def draw(self, projection, view):
        if not self.visible:
            return
        depth_was_enabled = GL.glIsEnabled(GL.GL_DEPTH_TEST)
        blend_was_enabled = GL.glIsEnabled(GL.GL_BLEND)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        # The grid is a reference overlay, so it remains visible behind objects.
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glUseProgram(self.program)
        GL.glUniformMatrix4fv(GL.glGetUniformLocation(self.program, 'projection'), 1, True, projection)
        GL.glUniformMatrix4fv(GL.glGetUniformLocation(self.program, 'modelview'), 1, True, view)
        GL.glBindVertexArray(self.vao)
        GL.glLineWidth(1.0)
        GL.glDrawArrays(GL.GL_LINES, 0, self.count)
        GL.glBindVertexArray(0)
        if depth_was_enabled:
            GL.glEnable(GL.GL_DEPTH_TEST)
        if not blend_was_enabled:
            GL.glDisable(GL.GL_BLEND)
