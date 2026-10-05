from shapes.two_d.polygon import Polygon

class Pentagon(Polygon):
    def __init__(self, radius=0.5, shading='phong'):
        super().__init__(n=5, radius=radius, shading=shading)