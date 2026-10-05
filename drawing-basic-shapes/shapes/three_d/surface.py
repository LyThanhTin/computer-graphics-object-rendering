import ast

import numpy as np
import OpenGL.GL as GL

from core.shape import Shape


class _FunctionValidator(ast.NodeVisitor):
    """
    Validate mathematical expressions before evaluating them.
    """

    ALLOWED_NAMES = {
        "x",
        "y",
        "pi",
        "e",
        "sin",
        "cos",
        "tan",
        "exp",
        "sqrt",
        "log",
        "abs",
    }

    ALLOWED_NODES = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Call,
        ast.Name,
        ast.Constant,
        ast.Load,
    )

    def visit(self, node):
        if not isinstance(node, self.ALLOWED_NODES):
            raise ValueError(
                f"Unsupported expression element: {type(node).__name__}"
            )
        super().visit(node)

    def visit_Name(self, node):
        if node.id not in self.ALLOWED_NAMES:
            raise ValueError(f"Unknown name: {node.id}")

    def visit_Constant(self, node):
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed.")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple mathematical functions are allowed.")

        if node.func.id not in self.ALLOWED_NAMES:
            raise ValueError(f"Unknown function: {node.func.id}")

        for arg in node.args:
            self.visit(arg)


class Surface(Shape):

    def __init__(
        self,
        function="sin(x) * cos(y)",
        xmin=-2.0,
        xmax=2.0,
        ymin=-2.0,
        ymax=2.0,
        x_segments=40,
        y_segments=40,
        shading="phong"
    ):
        super().__init__(shading)

        self.function = function

        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.x_segments = x_segments
        self.y_segments = y_segments

        # Compile and validate the function once.
        self._compiled_function = self._compile_function(function)

        self.vertices, self.normals = self._generate_mesh()
        self.vertex_count = len(self.vertices)

        self.colors = np.tile(
            np.array([[0.2, 0.7, 1.0]], dtype=np.float32),
            (self.vertex_count, 1)
        )

        self.setup()

    # Function handling
    def _compile_function(self, expression):
        expression = expression.replace("^", "**")

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise ValueError(
                f"Invalid mathematical expression: {expression}"
            ) from e

        _FunctionValidator().visit(tree)

        return compile(tree, "<surface>", "eval")

    def _function(self, x, y):
        namespace = {
            "x": x,
            "y": y,
            "pi": np.pi,
            "e": np.e,

            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "exp": np.exp,
            "sqrt": np.sqrt,
            "log": np.log,
            "abs": np.abs,
        }

        return eval(
            self._compiled_function,
            {"__builtins__": {}},
            namespace
        )

    # Geometry
    def _point(self, x, y):
        z = self._function(x, y)

        return [x, z, y]

    def _normal(self, x, y):
        """
        Numerical normal using central differences.

        For z = f(x, y):

            tangent_x = (1, fx, 0)
            tangent_y = (0, fy, 1)

        Their cross product gives a surface normal.
        """

        h = 1e-4
        fx = (self._function(x + h, y) - self._function(x - h, y)) / (2.0 * h)
        fy = (self._function(x, y + h) - self._function(x, y - h)) / (2.0 * h)

        normal = np.array([-fx, 1.0, -fy], dtype=np.float32)
        length = np.linalg.norm(normal)

        if length > 1e-8:
            normal /= length

        return normal

    def _generate_mesh(self):
        vertices = []
        normals = []

        dx = (self.xmax - self.xmin) / self.x_segments
        dy = (self.ymax - self.ymin) / self.y_segments

        for i in range(self.x_segments):
            x1 = self.xmin + i * dx
            x2 = self.xmin + (i + 1) * dx

            for j in range(self.y_segments):
                y1 = self.ymin + j * dy
                y2 = self.ymin + (j + 1) * dy

                p1 = self._point(x1, y1)
                p2 = self._point(x2, y1)
                p3 = self._point(x2, y2)
                p4 = self._point(x1, y2)

                n1 = self._normal(x1, y1)
                n2 = self._normal(x2, y1)
                n3 = self._normal(x2, y2)
                n4 = self._normal(x1, y2)

                # Triangle 1
                vertices.extend([p1, p2, p3])
                normals.extend([n1, n2, n3])

                # Triangle 2
                vertices.extend([p1, p3, p4])
                normals.extend([n1, n3, n4])

        return (
            np.array(vertices, dtype=np.float32),
            np.array(normals, dtype=np.float32)
        )

    def setup(self):
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors,   ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals,  ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.setup_shaders()