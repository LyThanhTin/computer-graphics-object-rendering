from ellipse import Ellipse


class Circle(Ellipse):
    def __init__(
        self,
        radius=0.5,
        segments=32,
        shading='phong'
    ):
        super().__init__(
            rx=radius,
            ry=radius,
            segments=segments,
            shading=shading
        )