import numpy as np


class PLYLoader:
    """
    ASCII PLY loader.

    Supports:
        vertex:
            x y z
            optional nx ny nz
            optional red green blue

        face:
            vertex index list

    Faces with more than 3 vertices are triangulated
    using a triangle fan.
    """

    def __init__(self, filename):
        self.filename = filename

        self.vertex_count = 0
        self.face_count = 0

        self.vertex_properties = []
        self.header_end = None

    # =============================================================
    # Public API
    # =============================================================

    def load(self):
        with open(self.filename, "r", encoding="utf-8") as file:
            lines = file.readlines()

        self._parse_header(lines)

        # Remove empty/comment lines from the data section.
        data_lines = []

        for line in lines[self.header_end + 1:]:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue

            data_lines.append(line)

        vertex_lines = data_lines[:self.vertex_count]
        face_lines = data_lines[
            self.vertex_count:
            self.vertex_count + self.face_count
        ]

        vertices = []
        normals = []
        colors = []
        indices = []

        # Vertices
        for line in vertex_lines:
            values = line.split()

            if len(values) < len(self.vertex_properties):
                raise ValueError(
                    f"Invalid vertex line in {self.filename}:\n"
                    f"{line}\n"
                    f"Expected {len(self.vertex_properties)} values, "
                    f"got {len(values)}."
                )

            properties = {}

            for i, name in enumerate(self.vertex_properties):
                properties[name] = values[i]

            vertices.append([
                float(properties["x"]),
                float(properties["y"]),
                float(properties["z"])
            ])

            if all(name in properties for name in ("nx", "ny", "nz")):
                normals.append([
                    float(properties["nx"]),
                    float(properties["ny"]),
                    float(properties["nz"])
                ])

            if all(name in properties for name in ("red", "green", "blue")):
                colors.append([
                    self._normalize_color(
                        float(properties["red"])
                    ),
                    self._normalize_color(
                        float(properties["green"])
                    ),
                    self._normalize_color(
                        float(properties["blue"])
                    )
                ])

        # Faces
        for line in face_lines:
            values = line.split()
            if not values:
                continue
            count = int(values[0])
            face = [int(v) for v in values[1:count + 1]]

            if len(face) < 3:
                continue

            # Triangle fan
            #
            # 0 1 2 3
            #
            # becomes:
            #
            # 0 1 2
            # 0 2 3

            for i in range(1, len(face) - 1):
                indices.extend([
                    face[0],
                    face[i],
                    face[i + 1]
                ])

        vertices = np.asarray(vertices, dtype=np.float32)
        indices = np.asarray(indices, dtype=np.uint32)

        # Normals
        if len(normals) == self.vertex_count:
            normals = np.asarray(normals, dtype=np.float32)
        else:
            normals = self._compute_normals(vertices, indices)

        # Colors
        if len(colors) == self.vertex_count:
            colors = np.asarray(colors, dtype=np.float32)
        else:
            colors = None

        return vertices, normals, colors, indices

    # =============================================================
    # Header
    # =============================================================

    def _parse_header(self, lines):
        if not lines:
            raise ValueError(
                f"Empty PLY file: {self.filename}"
            )

        if lines[0].strip() != "ply":
            raise ValueError(
                f"Not a PLY file: {self.filename}"
            )

        current_element = None

        for i, line in enumerate(lines[1:], start=1):
            parts = line.strip().split()

            if not parts:
                continue

            command = parts[0]

            if command == "format":
                if len(parts) < 2:
                    raise ValueError(
                        "Invalid PLY format declaration."
                    )

                if parts[1] != "ascii":
                    raise ValueError(
                        "Only ASCII PLY is currently supported."
                    )

            elif command == "element":
                current_element = parts[1]

                if current_element == "vertex":
                    self.vertex_count = int(parts[2])

                elif current_element == "face":
                    self.face_count = int(parts[2])

            elif command == "property":
                if current_element == "vertex":
                    # property float x
                    # property float nx
                    # property uchar red
                    #
                    # We only need the property name.
                    self.vertex_properties.append(parts[-1])

            elif command == "end_header":
                self.header_end = i
                break

        if self.header_end is None:
            raise ValueError(
                "PLY header does not contain end_header."
            )

    # =============================================================
    # Utilities
    # =============================================================

    @staticmethod
    def _normalize_color(value):
        # PLY colors are commonly 0-255.
        if value > 1.0:
            return value / 255.0

        return value

    @staticmethod
    def _compute_normals(vertices, indices):
        normals = np.zeros_like(vertices)

        for i in range(0, len(indices), 3):
            i0 = indices[i]
            i1 = indices[i + 1]
            i2 = indices[i + 2]

            a = vertices[i0]
            b = vertices[i1]
            c = vertices[i2]

            normal = np.cross(b - a, c - a)
            length = np.linalg.norm(normal)

            if length > 1e-8:
                normal /= length

            normals[i0] += normal
            normals[i1] += normal
            normals[i2] += normal

        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        lengths[lengths < 1e-8] = 1.0
        normals /= lengths

        return normals


# =============================================================
# Convenience function
# =============================================================

def load_ply(filename, shading='phong'):
    from core.mesh import Mesh
    loader = PLYLoader(filename)
    vertices, normals, colors, indices = loader.load()
    return Mesh(vertices=vertices, normals=normals, colors=colors, indices=indices, shading=shading)