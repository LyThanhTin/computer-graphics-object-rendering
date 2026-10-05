"""GLFW window and render loop shared by basicdemo samples."""
from itertools import cycle
from core.shape_factory import create_shape

import OpenGL.GL as GL
import glfw
import os

from .hud import HelpOverlay, help_text
from .transform import Trackball, identity, ortho
from .gui import GUI

class Viewer:
    """GLFW window: OpenGL 3.3 core, drawable list, W wireframe, Q/Esc to quit."""

    def __init__(self, width=640, height=480, title="Viewer",
                 clear_color=(0.5, 0.5, 0.5, 0.1), depth=False):
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)

        self.depth = depth
        self._title = title

        self.selected = None
        self.projection = ortho(-1, 1, -1, 1, -1, 1)
        self.view = identity()

        self.win = glfw.create_window(width, height, title, None, None)
        if not self.win:
            raise RuntimeError("Failed to create GLFW window")
        glfw.maximize_window(self.win)
        glfw.make_context_current(self.win)
        fw, fh = glfw.get_framebuffer_size(self.win)
        GL.glViewport(0, 0, fw, fh)
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_mouse_button_callback(self.win, self.on_mouse_button)

        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        GL.glClearColor(*clear_color)
        if depth:
            GL.glEnable(GL.GL_DEPTH_TEST)
            GL.glDepthFunc(GL.GL_LESS)

        self.fill_modes = cycle([GL.GL_LINE, GL.GL_POINT, GL.GL_FILL])
        self._polygon_mode = GL.GL_FILL
        self.drawables = []
        self.show_help = True
        self._hud = None
        self._gui = None
        self.name = self.__class__.__name__

    def add(self, *drawables):
        for drawable in drawables:
            drawable.name = (
                f"{drawable.__class__.__name__} "
                f"{len(self.drawables) + 1}"
            )

            self.drawables.append(drawable)

        if self.selected is None and self.drawables:
            self.selected = self.drawables[0]

        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

        return drawables[-1] if drawables else None

    def _draw_matrices(self):
        """projection, view, model passed to drawable.draw(); None if unused."""
        return self.projection, self.view, None

    def _set_window_title(self):
        if self.selected is None:
            glfw.set_window_title(
            self.win,
            self._title
            )
            return

        index = self.drawables.index(self.selected) + 1
        
        glfw.set_window_title(
            self.win,
            f"{self._title} | "
            f"Selected: [{index}/{len(self.drawables)}] "
            f"{type(self.selected).__name__}"
        )

    def _ensure_hud(self):
        if self._hud is None:
            self._hud = HelpOverlay()
        self._hud.refresh(self)

    def _ensure_gui(self):
        if self._gui is None:
            self._gui = GUI(self)

    def run(self):
        self._set_window_title()
        self._ensure_hud()
        print()
        print(help_text(self))
        print('  (Press H to hide or show the on-screen help.)')
        print()

        fw, fh = glfw.get_framebuffer_size(self.win)
        GL.glViewport(0, 0, fw, fh)

        clear = GL.GL_COLOR_BUFFER_BIT
        if self.depth:
            clear |= GL.GL_DEPTH_BUFFER_BIT
        while not glfw.window_should_close(self.win):
            fw, fh = glfw.get_framebuffer_size(self.win)
            GL.glViewport(0, 0, fw, fh)
            
            GL.glClear(clear)
            projection, view, model = self._draw_matrices()
            for drawable in self.drawables:
                drawable.draw(projection, view, model)
            if self.show_help:
                self._ensure_hud()
                self._hud.draw(self.win)
            self._ensure_gui()
            self._gui.draw()
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self._polygon_mode)
            glfw.swap_buffers(self.win)
            glfw.poll_events()

    def on_key(self, _win, key, _scancode, action, _mods):
        if action != glfw.PRESS and action != glfw.REPEAT:
            return
        if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
            glfw.set_window_should_close(self.win, True)
        elif action == glfw.PRESS and key == glfw.KEY_W:
            self._polygon_mode = next(self.fill_modes)
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self._polygon_mode)
        elif action == glfw.PRESS and key == glfw.KEY_H:
            self.show_help = not self.show_help
        elif key == glfw.KEY_1:
            self.add(Cube())
        elif key == glfw.KEY_2:
            self.add(Sphere())
        elif key == glfw.KEY_3:
            self.add(Cylinder())
        elif key == glfw.KEY_4:
            self.add(Torus())
        elif action == glfw.PRESS and key == glfw.KEY_DELETE:
            self.delete_selected()
            return
        elif key == glfw.KEY_DELETE:
            self.delete_selected()
            return
        elif action == glfw.PRESS and key == glfw.KEY_TAB:
            self.select_next()
            return
        if self.selected is not None:
            if hasattr(self.selected, 'key_handler'):
                self.selected.key_handler(key)
        if self._hud is not None:
            self._hud.refresh(self)

    def select_next(self):
        if not self.drawables:
            return

        if self.selected is None:
            self.selected = self.drawables[0]
        else:
            index = self.drawables.index(self.selected)
            self.selected = self.drawables[(index + 1) % len(self.drawables)]

        self._set_window_title()

    def add_shape(self, name):
        """
        Create a shape through the factory used by main.py.
        """

        if not hasattr(self, 'shape_factory'):
            raise RuntimeError(
                "Viewer.shape_factory has not been configured."
            )

        drawable = self.shape_factory(name)

        self.add(drawable)

        # Give newly-created objects a small offset
        # so multiple objects don't occupy exactly
        # the same location.
        index = len(self.drawables) - 1

        if index > 0:
            x = ((index - 1) % 4 - 1.5) * 1.0
            y = ((index - 1) // 4) * 1.0

            drawable.translate(x, y, 0)

        self.selected = drawable

        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

    def delete_selected(self):
        if self.selected is None:
            return

        if self.selected not in self.drawables:
            self.selected = None
            return

        index = self.drawables.index(self.selected)

        self.drawables.pop(index)

        if not self.drawables:
            self.selected = None
        else:
            self.selected = self.drawables[min(index, len(self.drawables) - 1)]

        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

    def on_mouse_button(self, win, button, action, mods):
        if button != glfw.MOUSE_BUTTON_LEFT:
            return
        if action != glfw.PRESS:
            return
        if self._gui is None:
            return

        xpos, ypos = glfw.get_cursor_pos(win)

        self._gui.handle_mouse(xpos, ypos)

    def import_obj(self, filename):
        from loaders.obj_loader import load_obj

        drawable = load_obj(filename)
        drawable.name = os.path.basename(filename)

        self.add(drawable)
        self.selected = drawable
        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

    def import_ply(self, filename):
        from loaders.ply_loader import load_ply

        drawable = load_ply(filename)
        drawable.name = os.path.basename(filename)

        self.add(drawable)
        self.selected = drawable
        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

    def transform_selected(self, action):
        if self.selected is None:
            return

        obj = self.selected

        if action == "left":
            obj.translate(-0.1, 0, 0)
        elif action == "right":
            obj.translate(0.1, 0, 0)
        elif action == "up":
            obj.translate(0, 0.1, 0)
        elif action == "down":
            obj.translate(0, -0.1, 0)
        elif action == "forward":
            obj.translate(0, 0, 0.1)
        elif action == "backward":
            obj.translate(0, 0, -0.1)
        elif action == "rotate":
            obj.rotate(axis=(0, 1, 0), angle=10)
        elif action == "scale_up":
            obj.scale(1.1)
        elif action == "scale_down":
            obj.scale(0.9)
        elif action == "reset":
            obj.reset_transform()

        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

    def add_surface(self, function, xmin=-2.0, xmax=2.0, ymin=-2.0, ymax=2.0):
        from shapes.three_d.surface import Surface

        surface = Surface(
            function=function,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            x_segments=40,
            y_segments=40
        )
        self.add(surface)
        self._set_window_title()

        if self._gui is not None:
            self._gui.refresh()

        return surface

class TrackballViewer(Viewer):
    """Viewer with depth test and trackball camera."""

    def __init__(self, width=800, height=800, title="Viewer",
                 clear_color=(0.5, 0.5, 0.5, 0.1)):
        glfw.window_hint(glfw.DEPTH_BITS, 16)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        super().__init__(width, height, title, clear_color, depth=True)

        self.trackball = Trackball()
        self.mouse = (0, 0)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        glfw.set_scroll_callback(self.win, self.on_scroll)

    def _draw_matrices(self):
        win_size = glfw.get_window_size(self.win)
        view = self.trackball.view_matrix()
        projection = self.trackball.projection_matrix(win_size)
        return projection, view, None

    def on_mouse_move(self, win, xpos, ypos):
        # GUI occupies the top-left region.
        if self._gui is not None:
            if (xpos <= self._gui.margin + self._gui.width and
                ypos <= self._gui.margin + self._gui.image.shape[0]):
                return
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.trackball.drag(old, self.mouse, glfw.get_window_size(win))
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.trackball.pan(old, self.mouse)

    def on_scroll(self, win, _deltax, deltay):
        self.trackball.zoom(deltay, glfw.get_window_size(win)[1])
    
    def delete_selected(self):
        if self.selected is None:
            return

        if self.selected not in self.drawables:
            self.selected = None
            return

        index = self.drawables.index(self.selected)

        self.drawables.remove(self.selected)

        if not self.drawables:
            self.selected = None
        else:
            index = min(index, len(self.drawables) - 1)
            self.selected = self.drawables[index]

        self._set_window_title()