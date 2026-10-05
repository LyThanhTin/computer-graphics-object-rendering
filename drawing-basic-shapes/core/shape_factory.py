from shapes.two_d.triangle import Triangle
from shapes.two_d.rectangle import Rectangle
from shapes.two_d.trapezoid import Trapezoid
from shapes.two_d.ellipse import Ellipse
from shapes.two_d.circle import Circle
from shapes.two_d.star import Star
from shapes.two_d.arrow import Arrow
from shapes.two_d.pentagon import Pentagon
from shapes.two_d.hexagon import Hexagon

from shapes.three_d.cube import Cube
from shapes.three_d.cylinder import Cylinder
from shapes.three_d.cone import Cone
from shapes.three_d.sphere import Sphere
from shapes.three_d.truncated_cone import TruncatedCone
from shapes.three_d.tetrahedron import Tetrahedron
from shapes.three_d.torus import Torus
from shapes.three_d.surface import Surface
from shapes.three_d.prism import Prism

SHAPE_FACTORIES = {
    "Triangle": Triangle,
    "Rectangle": Rectangle,
    "Pentagon": Pentagon,
    "Hexagon": Hexagon,
    "Trapezoid": Trapezoid,
    "Ellipse": Ellipse,
    "Circle": Circle,
    "Star": Star,
    "Arrow": Arrow,

    "Cube": Cube,
    "Cylinder": Cylinder,
    "Cone": Cone,
    "Sphere": Sphere,
    "Truncated Cone": TruncatedCone,
    "Tetrahedron": Tetrahedron,
    "Torus": Torus,
    "Prism": Prism,
    "Surface": Surface,
}


def create_shape(name):
    if name not in SHAPE_FACTORIES:
        raise ValueError(
            f"Unknown shape: {name}"
        )

    return SHAPE_FACTORIES[name]()