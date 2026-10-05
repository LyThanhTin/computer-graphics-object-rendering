from shapes.two_d.polygon import Polygon

class Triangle(Polygon):
    def __init__(self, radius=0.5, shading='phong'):
        super().__init__(n=3, radius=radius, shading=shading)