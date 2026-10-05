from shapes.two_d.polygon import Polygon

class Hexagon(Polygon):
    def __init__(self, radius=0.5, shading='phong'):
        super().__init__(n=6, radius=radius, shading=shading)