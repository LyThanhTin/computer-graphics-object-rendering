import ctypes
import os

import glfw
import numpy as np
import OpenGL.GL as GL
from PIL import Image, ImageDraw, ImageFont

from .shader import Shader
from tkinter import Tk, filedialog, simpledialog, messagebox

_VERT = """
#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texcoord;
out vec2 v_uv;
void main()
{
    v_uv = texcoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

_FRAG = """
#version 330 core
in vec2 v_uv;
uniform sampler2D gui_texture;
out vec4 out_color;
void main()
{
    out_color = texture(gui_texture, v_uv);
}
"""

_FONT_CANDIDATES = (
    'C:\\Windows\\Fonts\\segoeui.ttf',
    'C:\\Windows\\Fonts\\arial.ttf',
    'C:\\Windows\\Fonts\\consola.ttf',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
)

def _font(size):
    for path in _FONT_CANDIDATES:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()

class GUI:
    """
    Lightweight OpenGL GUI.

    Uses Pillow to generate the panel texture and
    OpenGL to display it.

    The GUI itself does not create or own shapes.
    It communicates with Viewer through callbacks.
    """

    def __init__(self, viewer):
        self.viewer = viewer
        self.width = 360
        self.margin = 15
        self.image = None
        self.buttons = []
        self.shader = Shader(_VERT, _FRAG)
        self.texture = GL.glGenTextures(1)
        self.vao = GL.glGenVertexArrays(1)
        self.vbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, 4 * 4 * 4, None, GL.GL_DYNAMIC_DRAW)
        
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, False, 16, None)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, False, 16, ctypes.c_void_p(8))
        GL.glEnableVertexAttribArray(1)
        
        GL.glBindVertexArray(0)
        GL.glUseProgram(self.shader.render_idx)
        
        location = GL.glGetUniformLocation(
            self.shader.render_idx,
            'gui_texture'
        )
        GL.glUniform1i(location, 0)
        self.refresh()

    # =============================================================
    # Rendering
    # =============================================================

    def refresh(self):
        self.buttons = []
        img = self._render()
        self.image = np.ascontiguousarray(
            np.array(img, dtype=np.uint8)
        )
        self._upload_texture()

    def _upload_texture(self):
        if self.image is None:
            return

        h, w = self.image.shape[:2]

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA,
            w,
            h,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            self.image
        )

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MIN_FILTER,
            GL.GL_LINEAR
        )

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MAG_FILTER,
            GL.GL_LINEAR
        )

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_WRAP_S,
            GL.GL_CLAMP_TO_EDGE
        )

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_WRAP_T,
            GL.GL_CLAMP_TO_EDGE
        )

    def draw(self):
        if self.image is None:
            return

        fw, fh = glfw.get_framebuffer_size(self.viewer.win)
        pw, ph = self.image.shape[1], self.image.shape[0]
        margin = self.margin

        x0 = -1.0 + 2.0 * margin / fw
        x1 = x0 + 2.0 * pw / fw

        y1 = 1.0 - 2.0 * margin / fh
        y0 = y1 - 2.0 * ph / fh

        quad = np.array([
            [x0, y1, 0.0, 0.0],
            [x0, y0, 0.0, 1.0],
            [x1, y1, 1.0, 0.0],
            [x1, y0, 1.0, 1.0],
        ], dtype=np.float32)

        old_depth = GL.glIsEnabled(
            GL.GL_DEPTH_TEST
        )

        old_blend = GL.glIsEnabled(
            GL.GL_BLEND
        )

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_BLEND)

        GL.glBlendFunc(
            GL.GL_SRC_ALPHA,
            GL.GL_ONE_MINUS_SRC_ALPHA
        )

        GL.glPolygonMode(
            GL.GL_FRONT_AND_BACK,
            GL.GL_FILL
        )

        GL.glUseProgram(self.shader.render_idx)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, quad)
        
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        
        GL.glBindVertexArray(0)

        if old_depth:
            GL.glEnable(GL.GL_DEPTH_TEST)

        if not old_blend:
            GL.glDisable(GL.GL_BLEND)

    # =============================================================
    # GUI layout
    # =============================================================

    def _render(self):
        font = _font(16)
        button_font = _font(13)
        title_font = _font(20)

        width = self.width

        # ---------------------------------------------------------
        # Layout constants
        # ---------------------------------------------------------

        x = 18

        button_width = 110
        button_height = 32

        gap_x = 8
        gap_y = 8

        columns = 3

        # ---------------------------------------------------------
        # Shape lists
        # ---------------------------------------------------------

        shapes_2d = [
            "Triangle",
            "Rectangle",
            "Pentagon",
            "Hexagon",
            "Circle",
            "Ellipse",
            "Trapezoid",
            "Star",
            "Arrow",
        ]

        shapes_3d = [
            "Cube",
            "Sphere",
            "Cylinder",
            "Cone",
            "Truncated Cone",
            "Tetrahedron",
            "Torus",
            "Prism",
            "Surface",
        ]

        transform_buttons = [
            ("←", "left"),
            ("→", "right"),
            ("↑", "up"),
            ("↓", "down"),
            ("Forward", "forward"),
            ("Backward", "backward"),
            ("Rotate", "rotate"),
            ("Scale +", "scale_up"),
            ("Scale -", "scale_down"),
            ("Reset", "reset"),
        ]

        # ---------------------------------------------------------
        # Calculate required height
        # ---------------------------------------------------------

        y = 15

        # Title
        y += 38

        # Objects title
        y += 30

        # Existing objects
        y += len(self.viewer.drawables) * 32

        # 2D section
        y += 15
        y += 32

        rows_2d = (len(shapes_2d) + columns - 1) // columns
        y += rows_2d * (button_height + 8)

        # 3D section
        y += 15
        y += 32

        rows_3d = (len(shapes_3d) + columns - 1) // columns
        y += rows_3d * (button_height + 8)

        # Import
        y += 15
        y += 32
        y += 50

        # Transform
        y += 10
        y += 32

        rows_transform = (len(transform_buttons) + columns - 1) // columns
        y += rows_transform * (button_height + 8)

        # Delete
        y += 15
        y += 36

        height = y + 20

        # ---------------------------------------------------------
        # Create image
        # ---------------------------------------------------------

        img = Image.new(
            "RGBA",
            (width, height),
            (18, 18, 24, 235)
        )

        draw = ImageDraw.Draw(img)

        y = 15

        # =========================================================
        # Title
        # =========================================================

        draw.text(
            (x, y),
            "ASSIGNMENT 1",
            font=title_font,
            fill=(90, 220, 255, 255)
        )

        y += 38

        # =========================================================
        # Objects
        # =========================================================

        draw.text((x, y), "Objects", font=font, fill=(255, 255, 255, 255))
        y += 30

        for index, obj in enumerate(self.viewer.drawables):
            selected = (obj is self.viewer.selected)
            if selected:
                draw.rectangle(
                    (10, y - 4, width - 10, y + 24),
                    fill=(60, 90, 110, 220)
                )
            name = (f"{index + 1}. " f"{obj.name}")
            draw.text((x, y), name, font=font, fill=((90, 220, 255, 255) if selected else (240, 240, 240, 255)))

            self.buttons.append({
                "type": "select",
                "index": index,
                "rect": (10, y - 4, width - 10, y + 24)
            })
            y += 32

        # =========================================================
        # Helper for shape buttons
        # =========================================================

        def draw_button_grid(shapes, surface_name=None):
            nonlocal y
            for i, name in enumerate(shapes):
                row = i // columns
                col = i % columns
                bx = (12 + col * (button_width + gap_x))
                by = (y + row * (button_height + gap_y))
                draw.rectangle(
                    (bx, by, bx + button_width, by + button_height),
                    fill=(45, 45, 55, 255),
                    outline=(90, 90, 105, 255)
                )
                draw.text(
                    (bx + 7, by + 8),
                    name,
                    font=button_font,
                    fill=(240, 240, 240, 255)
                )
                button_type = (
                    "surface"
                    if name == surface_name
                    else "add"
                )
                self.buttons.append({
                    "type": button_type,
                    "name": name,
                    "rect": (bx, by, bx + button_width, by + button_height)
                })

            rows = (len(shapes) + columns - 1) // columns
            y += rows * (button_height + gap_y)

        # =========================================================
        # 2D Shapes
        # =========================================================
        
        y += 15
        draw.text((x, y), "2D Shapes", font=font, fill=(255, 255, 255, 255))
        y += 32
        draw_button_grid(shapes_2d)

        # =========================================================
        # 3D Shapes
        # =========================================================

        y += 15
        draw.text((x, y), "3D Shapes", font=font, fill=(255, 255, 255, 255))
        y += 32

        # Surface gets its own button type.
        draw_button_grid(shapes_3d, surface_name="Surface")

        # Fix Surface button type.
        for button in self.buttons:
            if (button["type"] == "add" and button.get("name") == "Surface"):
                button["type"] = "surface"

        # =========================================================
        # Import section
        # =========================================================

        y += 15
        draw.text((x, y), "Import Model", font=font, fill=(255, 255, 255, 255))
        y += 32
        import_buttons = [("Import OBJ", "obj"), ("Import PLY", "ply"),]

        for i, (label, file_type) in enumerate(import_buttons):
            bx = (12 + i * (button_width + gap_x))
            by = y
            draw.rectangle(
                (bx, by, bx + button_width, by + button_height),
                fill=(45, 45, 55, 255),
                outline=(90, 90, 105, 255)
            )
            draw.text(
                (bx + 7, by + 8),
                label,
                font=button_font,
                fill=(240, 240, 240, 255)
            )
            self.buttons.append({
                "type": "import",
                "format": file_type,
                "rect": (bx, by, bx + button_width, by + button_height)
            })
        y += 50

        # =========================================================
        # Transform section
        # =========================================================

        y += 10
        draw.text((x, y), "Transform", font=font, fill=(255, 255, 255, 255))
        y += 32

        for i, (label, action) in enumerate(transform_buttons):
            row = i // columns
            col = i % columns
            bx = (12 + col * (button_width + gap_x))
            by = (y + row * (button_height + gap_y))
            draw.rectangle(
                (bx, by, bx + button_width, by + button_height),
                fill=(45, 45, 55, 255),
                outline=(90, 90, 105, 255)
            )
            draw.text(
                (bx + 7, by + 8),
                label,
                font=button_font,
                fill=(240, 240, 240, 255)
            )
            self.buttons.append({
                "type": "transform",
                "action": action,
                "rect": (bx, by, bx + button_width, by + button_height)
            })
        rows_transform = (len(transform_buttons) + columns - 1) // columns
        y += rows_transform * (button_height + gap_y)

        # =========================================================
        # Delete
        # =========================================================

        y += 15
        draw.rectangle(
            (12, y, width - 12, y + 36),
            fill=(100, 45, 45, 255),
            outline=(150, 70, 70, 255)
        )
        draw.text(
            (x, y + 8),
            "Delete Selected",
            font=font,
            fill=(255, 240, 240, 255)
        )
        self.buttons.append({
            "type": "delete",
            "rect": (12, y, width - 12, y + 36)
        })
        return img

    # =============================================================
    # Mouse interaction
    # =============================================================

    def handle_mouse(self, xpos, ypos):
        """
        xpos/ypos are window coordinates.

        Pillow panel uses top-left origin.
        """

        if xpos < self.margin:
            return False

        if xpos > self.margin + self.width:
            return False

        x = xpos - self.margin
        y = ypos - self.margin

        for button in self.buttons:
            x0, y0, x1, y1 = button["rect"]

            if x0 <= x <= x1 and y0 <= y <= y1:

                if button["type"] == "select":
                    index = button["index"]

                    if 0 <= index < len(self.viewer.drawables):
                        self.viewer.selected = (self.viewer.drawables[index])
                        self.viewer._set_window_title()
                        self.refresh()

                elif button["type"] == "add":
                    self.viewer.add_shape(button["name"])

                elif button["type"] == "surface":
                    self.create_surface()
                elif button["type"] == "delete":
                    self.viewer.delete_selected()
                elif button["type"] == "import":
                    if button["format"] == "obj":
                        self.import_obj()
                    elif button["format"] == "ply":
                        self.import_ply()
                    return True
                elif button["type"] == "transform":
                    self.viewer.transform_selected(button["action"])
                    return True
                return True

        return False

    def _choose_file(self, filetypes):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        filename = filedialog.askopenfilename(title="Import 3D Model", filetypes=filetypes)

        root.destroy()
        return filename

    def import_obj(self):
        filename = self._choose_file([("OBJ files", "*.obj"), ("All files", "*.*"),])
        if not filename:
            return
        self.viewer.import_obj(filename)


    def import_ply(self):
        filename = self._choose_file([("PLY files", "*.ply"), ("All files", "*.*"),])
        if not filename:
            return
        self.viewer.import_ply(filename)

    def create_surface(self):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        function = simpledialog.askstring(
            "Create Surface",
            "Enter z = f(x, y):",
            initialvalue="sin(x) * cos(y)",
            parent=root
        )

        if not function:
            root.destroy()
            return

        xmin = simpledialog.askfloat(
            "Surface Range",
            "xmin:",
            initialvalue=-2.0,
            parent=root
        )

        if xmin is None:
            root.destroy()
            return

        xmax = simpledialog.askfloat(
            "Surface Range",
            "xmax:",
            initialvalue=2.0,
            parent=root
        )

        if xmax is None:
            root.destroy()
            return

        ymin = simpledialog.askfloat(
            "Surface Range",
            "ymin:",
            initialvalue=-2.0,
            parent=root
        )

        if ymin is None:
            root.destroy()
            return

        ymax = simpledialog.askfloat(
            "Surface Range",
            "ymax:",
            initialvalue=2.0,
            parent=root
        )

        if ymax is None:
            root.destroy()
            return

        root.destroy()

        try:
            self.viewer.add_surface(
                function=function,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax
            )

        except Exception as e:
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            messagebox.showerror(
                "Surface Error",
                str(e),
                parent=root
            )

            root.destroy()