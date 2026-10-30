import ctypes
import os

import glfw
import numpy as np
import OpenGL.GL as GL
from PIL import Image, ImageDraw, ImageFont

from .shader import Shader
from tkinter import Tk, filedialog, simpledialog, messagebox, colorchooser
from pathlib import Path

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

_FONT_DIR = (
    Path(__file__).resolve().parent.parent
    / "drawing-basic-shapes"
    / "assets"
    / "fonts"
)

# Optional custom fonts. If they are not installed in assets/fonts, the GUI
# gracefully falls back to fonts available on the current operating system.
_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _font(size):
    for path in _FONT_CANDIDATES:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def _load_font(filename, size, fallback_size=None):
    """Load a project-local font, falling back safely when it is missing."""
    path = _FONT_DIR / filename
    if path.is_file():
        try:
            return ImageFont.truetype(str(path), size)
        except (OSError, ValueError):
            pass
    return _font(fallback_size if fallback_size is not None else size)

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
        # Object names live in their own clipped viewport. The rest of the
        # panel stays at a fixed height regardless of the number of objects.
        self.object_scroll_offset = 0
        self.object_row_height = 30
        self.object_list_height = 110
        self.object_list_rect = (12, 0, self.width - 12, 0)
        self.object_scrollbar_dragging = False
        self._scroll_drag_grab_y = 0
        self._scroll_drag_start_offset = 0
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
        # Holographic / cybercore typography. Put the TTF files in
        # drawing-basic-shapes/assets/fonts/ (see notes below).
        font = _load_font("Rajdhani-Medium.ttf", 17, fallback_size=16)
        button_font = _load_font("ShareTechMono-Regular.ttf", 13, fallback_size=13)
        title_font = _load_font("Orbitron-Bold.ttf", 19, fallback_size=20)

        width = self.width

        # ---------------------------------------------------------
        # Layout constants
        # ---------------------------------------------------------

        x = 18

        button_width = 110
        button_height = 28

        gap_x = 8
        gap_y = 5

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
            ("Left", "left"),
            ("Right", "right"),
            ("Up", "up"),
            ("Down", "down"),
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
        y += 38  # grid toggle control

        # Objects title + fixed-height clipped list viewport
        y += 30
        y += self.object_list_height + 10

        # 2D section
        y += 15
        y += 32

        rows_2d = (len(shapes_2d) + columns - 1) // columns
        y += rows_2d * (button_height + gap_y)

        # 3D section
        y += 15
        y += 32

        rows_3d = (len(shapes_3d) + columns - 1) // columns
        y += rows_3d * (button_height + gap_y)

        # Atoms and molecules
        y += 15
        y += 32
        part2_buttons = [
            ("Bohr H", "bohr:H"),
            ("Bohr C", "bohr:C"),
            ("Bohr O", "bohr:O"),
            ("Molecule H2O", "molecule:H2O"),
            ("Molecule CO2", "molecule:CO2"),
            ("Toggle Orbit", "toggle_orbit"),
        ]
        rows_part2 = (len(part2_buttons) + columns - 1) // columns
        y += rows_part2 * (button_height + gap_y)

        # Import
        y += 15
        y += 32
        y += 50
        y += 42

        # Transform
        y += 10
        y += 32

        rows_transform = (len(transform_buttons) + columns - 1) // columns
        y += rows_transform * (button_height + gap_y)

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
            (10, 7, 28, 242)
        )

        draw = ImageDraw.Draw(img)

        y = 15

        # =========================================================
        # Title
        # =========================================================

        # Cybercore / Y2K header with a bright neon accent rule.
        draw.rounded_rectangle((8, 7, width - 8, 47), radius=8,
                               fill=(24, 12, 48, 245), outline=(0, 220, 255, 220), width=1)
        draw.text((x, y), "3D GEOMETRY LAB", font=title_font, fill=(90, 235, 255, 255))
        
        y += 38

        grid_label = "GRID - XYZ (R) :  ON" if (self.viewer.world_grid is not None and self.viewer.world_grid.visible) else "GRID - XYZ (R) :  OFF"
        bx0, by0, bx1, by1 = (12, y, width - 12, y + 30)
        draw.rounded_rectangle((bx0, by0, bx1, by1), radius=6,
                               fill=(15, 49, 67, 255), outline=(0, 220, 255, 255), width=1)
        draw.text((x + 5, y + 7), grid_label, font=button_font, fill=(120, 245, 255, 255))
        self.buttons.append({"type": "toggle_grid", "rect": (bx0, by0, bx1, by1)})
        y += 38

        # =========================================================
        # Objects
        # =========================================================

        draw.text((x, y), "Objects", font=font, fill=(255, 255, 255, 255))
        y += 26

        # Draw the object names into a separate image, then paste it into a
        # fixed viewport. This clips all rows to the object-name box.
        list_top = y
        list_height = self.object_list_height
        list_left, list_right = 12, width - 12
        scrollbar_width = 10
        list_inner_right = list_right - scrollbar_width - 5
        self.object_list_rect = (list_left, list_top, list_right, list_top + list_height)

        draw.rounded_rectangle(
            (list_left, list_top, list_right, list_top + list_height),
            radius=6, fill=(14, 12, 36, 255), outline=(65, 105, 155, 255), width=1
        )

        list_layer = Image.new("RGBA", (list_right - list_left - 2, list_height - 2), (14, 12, 36, 255))
        list_draw = ImageDraw.Draw(list_layer)
        row_height = self.object_row_height
        count = len(self.viewer.drawables)
        max_offset = max(0, count * row_height - list_height)
        self.object_scroll_offset = max(0, min(self.object_scroll_offset, max_offset))
        first_index = max(0, self.object_scroll_offset // row_height)
        offset_in_row = self.object_scroll_offset % row_height
        visible_rows = (list_height + row_height - 1) // row_height + 1

        for index in range(first_index, min(count, first_index + visible_rows)):
            row_y = index * row_height - self.object_scroll_offset
            if row_y + row_height <= 0 or row_y >= list_height:
                continue
            selected = (self.viewer.drawables[index] is self.viewer.selected)
            local_y0 = row_y
            local_y1 = row_y + row_height
            if selected:
                list_draw.rounded_rectangle(
                    (2, local_y0 + 1, list_layer.width - 2, local_y1 - 2),
                    radius=4, fill=(43, 67, 100, 255), outline=(0, 220, 255, 255), width=1
                )
            name = f"{index + 1}. {self.viewer.drawables[index].name}"
            list_draw.text((8, row_y + 6), name, font=button_font,
                           fill=(90, 235, 255, 255) if selected else (232, 235, 255, 255))
            self.buttons.append({
                "type": "select", "index": index,
                "rect": (list_left + 2, list_top + row_y, list_inner_right, list_top + row_y + row_height),
                "clip_rect": self.object_list_rect,
            })

        img.alpha_composite(list_layer, (list_left + 1, list_top + 1))

        # A compact scrollbar is drawn only inside the object list box.
        track_x0 = list_right - scrollbar_width - 3
        track_x1 = list_right - 3
        track_y0 = list_top + 5
        track_y1 = list_top + list_height - 5
        draw.rounded_rectangle((track_x0, track_y0, track_x1, track_y1), radius=4,
                               fill=(31, 29, 58, 255), outline=(60, 90, 130, 255), width=1)
        content_height = max(list_height, count * row_height)
        thumb_height = max(24, int((track_y1 - track_y0) * list_height / content_height))
        travel = max(0, (track_y1 - track_y0) - thumb_height)
        thumb_y0 = track_y0 + (int(travel * self.object_scroll_offset / max_offset) if max_offset else 0)
        thumb_y1 = thumb_y0 + thumb_height
        draw.rounded_rectangle((track_x0 + 1, thumb_y0, track_x1 - 1, thumb_y1), radius=3,
                               fill=(0, 205, 245, 255) if max_offset else (66, 83, 115, 255))
        self.object_scrollbar_rect = (track_x0, track_y0, track_x1, track_y1)
        self.object_scrollbar_thumb_rect = (track_x0 + 1, thumb_y0, track_x1 - 1, thumb_y1)
        self.object_scroll_metrics = (max_offset, travel, thumb_height, track_y0)
        if max_offset > 0:
            self.buttons.append({
                "type": "object_scrollbar",
                "rect": (track_x0 - 2, track_y0, track_x1 + 2, track_y1),
            })
        y += list_height + 10

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
                    fill=(24, 22, 48, 255),
                    outline=(70, 145, 210, 255)
                )
                draw.text(
                    (bx + 7, by + 8),
                    name,
                    font=button_font,
                    fill=(205, 235, 255, 255)
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
        # Atoms and molecules
        # =========================================================

        y += 15
        draw.text((x, y), "Atoms & Molecules", font=font, fill=(255, 255, 255, 255))
        y += 32
        part2_buttons = [
            ("Bohr H", "bohr:H"),
            ("Bohr C", "bohr:C"),
            ("Bohr O", "bohr:O"),
            ("Molecule H2O", "molecule:H2O"),
            ("Molecule CO2", "molecule:CO2"),
            ("Toggle Orbit", "toggle_orbit"),
        ]
        for i, (label, action) in enumerate(part2_buttons):
            row = i // columns
            col = i % columns
            bx = 12 + col * (button_width + gap_x)
            by = y + row * (button_height + gap_y)
            draw.rectangle(
                (bx, by, bx + button_width, by + button_height),
                fill=(27, 25, 61, 255),
                outline=(220, 70, 210, 255)
            )
            draw.text((bx + 7, by + 8), label, font=button_font, fill=(240, 250, 255, 255))
            self.buttons.append({
                "type": "part2",
                "action": action,
                "rect": (bx, by, bx + button_width, by + button_height)
            })
        rows_part2 = (len(part2_buttons) + columns - 1) // columns
        y += rows_part2 * (button_height + gap_y)

        # =========================================================
        # Import section
        # =========================================================

        y += 15
        draw.text((x, y), "Import Model", font=font, fill=(255, 255, 255, 255))
        y += 32
        import_buttons = [("Import OBJ", "obj"), ("Import PLY", "ply"), ("Upload Texture", "texture")]

        for i, (label, file_type) in enumerate(import_buttons):
            bx = (12 + i * (button_width + gap_x))
            by = y
            draw.rectangle(
                (bx, by, bx + button_width, by + button_height),
                fill=(24, 22, 48, 255),
                outline=(0, 205, 245, 255)
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
        y += button_height + 8

        # =========================================================
        # Color controls
        # =========================================================
        y += 8
        draw.text((x, y), "Custom Colors", font=font, fill=(255, 255, 255, 255))
        y += 30
        bx0, by0, bx1, by1 = (12, y, width - 12, y + 34)
        draw.rounded_rectangle((bx0, by0, bx1, by1), radius=6,
                               fill=(45, 18, 66, 255), outline=(255, 55, 205, 255), width=1)
        draw.text((x + 5, y + 8), "COLOR - GRADIENT", font=button_font,
                  fill=(255, 155, 235, 255))
        self.buttons.append({"type": "color", "rect": (bx0, by0, bx1, by1)})
        y += 36

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
                fill=(24, 22, 48, 255),
                outline=(0, 205, 245, 255)
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

    def _panel_coords(self, xpos, ypos):
        """Convert GLFW cursor coordinates to panel-local coordinates."""
        return xpos - self.margin, ypos - self.margin

    def _inside_object_list(self, xpos, ypos):
        x, y = self._panel_coords(xpos, ypos)
        x0, y0, x1, y1 = self.object_list_rect
        return x0 <= x <= x1 and y0 <= y <= y1

    def handle_scroll(self, xpos, ypos, delta_y):
        """Scroll the object list only when the pointer is inside its box."""
        if not self._inside_object_list(xpos, ypos):
            return False
        max_offset = max(0, len(self.viewer.drawables) * self.object_row_height - self.object_list_height)
        if max_offset <= 0:
            return True
        self.object_scroll_offset = max(0, min(max_offset, self.object_scroll_offset - int(delta_y * self.object_row_height * 2)))
        self.refresh()
        return True

    def handle_mouse_move(self, xpos, ypos):
        """Update the list scrollbar while the left mouse button is held."""
        if not self.object_scrollbar_dragging:
            return False
        if not glfw.get_mouse_button(self.viewer.win, glfw.MOUSE_BUTTON_LEFT):
            self.object_scrollbar_dragging = False
            return False
        max_offset, travel, _thumb_height, track_y0 = self.object_scroll_metrics
        if max_offset <= 0 or travel <= 0:
            self.object_scrollbar_dragging = False
            return True
        panel_x, panel_y = self._panel_coords(xpos, ypos)
        delta_thumb = panel_y - self._scroll_drag_grab_y
        self.object_scroll_offset = int(self._scroll_drag_start_offset + delta_thumb * max_offset / travel)
        self.object_scroll_offset = max(0, min(max_offset, self.object_scroll_offset))
        self.refresh()
        return True

    def handle_mouse(self, xpos, ypos):
        """Handle clicks; coordinates use GLFW's top-left cursor origin."""
        if xpos < self.margin or xpos > self.margin + self.width:
            return False

        x, y = self._panel_coords(xpos, ypos)
        for button in self.buttons:
            x0, y0, x1, y1 = button["rect"]

            if x0 <= x <= x1 and y0 <= y <= y1:
                if button.get("clip_rect") is not None:
                    cx0, cy0, cx1, cy1 = button["clip_rect"]
                    if not (cx0 <= x <= cx1 and cy0 <= y <= cy1):
                        continue
                if button["type"] == "object_scrollbar":
                    max_offset, travel, thumb_height, track_y0 = self.object_scroll_metrics
                    thumb_y0, thumb_y1 = self.object_scrollbar_thumb_rect[1:4:2]
                    if thumb_y0 <= y <= thumb_y1:
                        self.object_scrollbar_dragging = True
                        self._scroll_drag_grab_y = y
                        self._scroll_drag_start_offset = self.object_scroll_offset
                    else:
                        track_height = max(1, self.object_scrollbar_rect[3] - self.object_scrollbar_rect[1])
                        self.object_scroll_offset = int(max_offset * (y - track_y0) / max(1, track_height))
                        self.object_scroll_offset = max(0, min(max_offset, self.object_scroll_offset))
                        self.refresh()
                    return True

                if button["type"] == "toggle_grid":
                    self.viewer.toggle_grid()
                    self.refresh()
                    return True
                if button["type"] == "color":
                    self.choose_color_mode()
                    return True
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
                elif button["type"] == "part2":
                    action = button["action"]
                    if action.startswith("bohr:"):
                        self.viewer.add_bohr_atom(action.split(":", 1)[1])
                    elif action.startswith("molecule:"):
                        self.viewer.add_molecule(action.split(":", 1)[1])
                    elif action == "toggle_orbit":
                        selected = self.viewer.selected
                        if selected is not None and hasattr(selected, "toggle_animation"):
                            selected.toggle_animation()
                    self.refresh()
                    return True
                elif button["type"] == "delete":
                    self.viewer.delete_selected()
                elif button["type"] == "import":
                    if button["format"] == "obj":
                        self.import_obj()
                    elif button["format"] == "ply":
                        self.import_ply()
                    elif button["format"] == "texture":
                        self.upload_texture()
                    return True
                elif button["type"] == "transform":
                    self.viewer.transform_selected(button["action"])
                    return True
                return True

        return False

    def choose_color_mode(self):
            """Apply a solid user-picked color or one of the Cyber Spectrum gradients."""
            selected = self.viewer.selected
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            try:
                if selected is None:
                    messagebox.showinfo("Color / Gradient", "Select an object first.", parent=root)
                    return
                if not hasattr(selected, "colors") or not hasattr(selected, "vertex_count"):
                    messagebox.showwarning("Color / Gradient",
                                           "This object does not expose editable vertex colors.",
                                           parent=root)
                    return
    
                mode = messagebox.askyesnocancel(
                    "Color / Gradient",
                    "Yes = Cyber Spectrum Gradient; No = Solid Color; Cancel = Keep Current.",
                    parent=root,
                )
                if mode is None:
                    return
    
                if mode is False:
                    picked = colorchooser.askcolor(title="Choose Shape Color", parent=root)[0]
                    if picked is None:
                        return
                    rgb = np.asarray(picked, dtype=np.float32) / 255.0
                    colors = np.tile(rgb, (selected.vertex_count, 1))
                else:
                    from core import palette
                    options = {
                        "blue-cyan": palette.CYBER_BLUE_CYAN,
                        "blue-violet": palette.CYBER_BLUE_VIOLET,
                        "cyan-violet": palette.CYBER_CYAN_VIOLET,
                        "violet-pink": palette.CYBER_VIOLET_PINK,
                        "orange-gold": palette.CYBER_ORANGE_GOLD,
                        "green-cyan": palette.CYBER_GREEN_CYAN,
                        "full-spectrum": palette.CYBER_FULL_SPECTRUM,
                    }
                    choice = simpledialog.askstring(
                        "Cyber Spectrum Gradient",
                        "Preset: blue-cyan, blue-violet, cyan-violet, violet-pink, "
                        "orange-gold, green-cyan, full-spectrum",
                        initialvalue="violet-pink", parent=root,
                    )
                    if not choice:
                        return
                    key = choice.strip().lower()
                    if key not in options:
                        messagebox.showerror("Unknown Gradient",
                                             "Please enter one of the listed preset names.",
                                             parent=root)
                        return
                    colors = palette.create_gradient_colors(selected.vertex_count, options[key])
    
                selected.colors = np.asarray(colors, dtype=np.float32)
                buffer_id = getattr(getattr(selected, "vao", None), "vbo", {}).get(1)
                if buffer_id is None:
                    messagebox.showerror("Color / Gradient", "Vertex-color buffer was not found.", parent=root)
                    return
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, buffer_id)
                GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, selected.colors.nbytes, selected.colors)
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
                self.viewer._set_window_title()
                self.refresh()
            finally:
                root.destroy()

    def _choose_file(self, filetypes, title="Import 3D Model"):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        try:
            filename = filedialog.askopenfilename(title=title, filetypes=filetypes, parent=root)
        finally:
            root.destroy()
        return filename

    def upload_texture(self):
        selected = self.viewer.selected
        if selected is None:
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showinfo("Upload Texture", "Please select a shape first.", parent=root)
            root.destroy()
            return
        if not hasattr(selected, "set_texture"):
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showwarning(
                "Upload Texture",
                "Texture upload is supported for regular shapes and imported meshes. Select one of those objects first.",
                parent=root,
            )
            root.destroy()
            return
        filename = self._choose_file([
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tga *.tif *.tiff"),
            ("All files", "*.*"),
        ], title="Choose Texture Image")
        if not filename:
            return
        try:
            selected.set_texture(filename)
            self.viewer._set_window_title()
            self.refresh()
        except Exception as exc:
            root = Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showerror("Texture Upload Failed", str(exc), parent=root)
            root.destroy()

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