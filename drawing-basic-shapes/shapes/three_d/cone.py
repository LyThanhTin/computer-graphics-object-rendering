from shapes.three_d.truncated_cone import TruncatedCone

class Cone(TruncatedCone):
    def __init__(self, radius=0.5, height=1.0, segments=32, shading='phong'):
        super().__init__(bottom_radius=radius, top_radius=0.0, height=height, segments=segments, shading=shading)