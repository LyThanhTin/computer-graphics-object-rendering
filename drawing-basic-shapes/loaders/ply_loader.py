
import struct
import numpy as np


class PLYLoader:
    """
    PLY loader supporting:
        - ASCII PLY
        - Binary little-endian PLY
        - Binary big-endian PLY

    Vertex properties:
        x, y, z
        optional nx, ny, nz
        optional red, green, blue

    Face properties:
        vertex_indices or vertex_index

    Polygon faces are triangulated using a triangle fan.
    """

    # PLY scalar types: aliases map to struct format and byte size.
    TYPE_MAP = {
        "char": ("b", 1),
        "int8": ("b", 1),
        "uchar": ("B", 1),
        "uint8": ("B", 1),
        "short": ("h", 2),
        "int16": ("h", 2),
        "ushort": ("H", 2),
        "uint16": ("H", 2),
        "int": ("i", 4),
        "int32": ("i", 4),
        "uint": ("I", 4),
        "uint32": ("I", 4),
        "float": ("f", 4),
        "float32": ("f", 4),
        "double": ("d", 8),
        "float64": ("d", 8),
    }

    def __init__(self, filename):
        self.filename = filename
        self.vertex_count = 0
        self.face_count = 0
        self.vertex_properties = []
        self.elements = []
        self.format = None

    def load(self):
        with open(self.filename, "rb") as file:
            self._parse_header(file)

            vertices = []
            normals = []
            colors = []
            faces = []

            if self.format == "ascii":
                self._read_ascii_data(
                    file, vertices, normals, colors, faces
                )
            else:
                self._read_binary_data(
                    file, vertices, normals, colors, faces
                )

        vertices = np.asarray(vertices, dtype=np.float32).reshape(-1, 3)

        indices = []
        for face in faces:
            if len(face) < 3:
                continue

            # Triangle fan: (0, 1, 2), (0, 2, 3), ...
            for i in range(1, len(face) - 1):
                indices.extend([face[0], face[i], face[i + 1]])

        indices = np.asarray(indices, dtype=np.uint32)

        if len(normals) == len(vertices):
            normals = np.asarray(normals, dtype=np.float32).reshape(-1, 3)
        else:
            normals = self._compute_normals(vertices, indices)

        if len(colors) == len(vertices):
            colors = np.asarray(colors, dtype=np.float32).reshape(-1, 3)
        else:
            colors = None

        if len(vertices) == 0:
            raise ValueError(f"No vertices found in PLY file: {self.filename}")

        if len(indices) and int(indices.max()) >= len(vertices):
            raise ValueError(
                f"Face index out of range in PLY file: {self.filename}"
            )

        return vertices, normals, colors, indices

    def _parse_header(self, file):
        first_line = file.readline().decode("ascii", errors="strict").strip()
        if first_line != "ply":
            raise ValueError(f"Not a PLY file: {self.filename}")

        current_element = None
        header_finished = False

        while True:
            raw_line = file.readline()
            if not raw_line:
                break

            line = raw_line.decode("ascii", errors="strict").strip()
            parts = line.split()

            if not parts or parts[0] in ("comment", "obj_info"):
                continue

            command = parts[0]

            if command == "format":
                if len(parts) < 3 or parts[2] != "1.0":
                    raise ValueError(f"Unsupported PLY format declaration: {line}")

                self.format = parts[1]
                if self.format not in (
                    "ascii",
                    "binary_little_endian",
                    "binary_big_endian",
                ):
                    raise ValueError(f"Unsupported PLY format: {self.format}")

            elif command == "element":
                if len(parts) != 3:
                    raise ValueError(f"Invalid PLY element declaration: {line}")

                current_element = {
                    "name": parts[1],
                    "count": int(parts[2]),
                    "properties": [],
                }
                self.elements.append(current_element)

                if parts[1] == "vertex":
                    self.vertex_count = int(parts[2])
                elif parts[1] == "face":
                    self.face_count = int(parts[2])

            elif command == "property":
                if current_element is None:
                    raise ValueError("PLY property appears before an element.")

                if len(parts) >= 2 and parts[1] == "list":
                    if len(parts) != 5:
                        raise ValueError(f"Invalid list property: {line}")

                    prop = {
                        "kind": "list",
                        "count_type": parts[2],
                        "item_type": parts[3],
                        "name": parts[4],
                    }
                else:
                    if len(parts) != 3:
                        raise ValueError(f"Invalid scalar property: {line}")

                    prop = {
                        "kind": "scalar",
                        "type": parts[1],
                        "name": parts[2],
                    }

                # Validate property types early.
                types = (
                    [prop["count_type"], prop["item_type"]]
                    if prop["kind"] == "list"
                    else [prop["type"]]
                )
                for type_name in types:
                    if type_name not in self.TYPE_MAP:
                        raise ValueError(
                            f"Unsupported PLY property type: {type_name}"
                        )

                current_element["properties"].append(prop)

                if current_element["name"] == "vertex":
                    self.vertex_properties.append(prop["name"])

            elif command == "end_header":
                header_finished = True
                break

        if not header_finished:
            raise ValueError("PLY header does not contain end_header.")

        if self.format is None:
            raise ValueError("PLY header does not specify a format.")

        if self.vertex_count <= 0:
            raise ValueError("PLY file contains no vertices.")

        required = {"x", "y", "z"}
        if not required.issubset(set(self.vertex_properties)):
            raise ValueError("PLY vertex properties must include x, y, and z.")

    def _read_ascii_data(self, file, vertices, normals, colors, faces):
        for element in self.elements:
            for _ in range(element["count"]):
                # Blank lines are harmless in ASCII PLY data. Skip them
                # before reading the next element record.
                while True:
                    line = file.readline()
                    if not line:
                        raise ValueError("Unexpected end of PLY data.")
                    values = line.decode("ascii", errors="strict").split()
                    if values:
                        break
                cursor = 0
                record = {}
                lists = {}

                for prop in element["properties"]:
                    name = prop["name"]

                    if prop["kind"] == "scalar":
                        if cursor >= len(values):
                            raise ValueError("Incomplete PLY data record.")

                        record[name] = float(values[cursor])
                        cursor += 1
                    else:
                        if cursor >= len(values):
                            raise ValueError("Incomplete PLY list property.")

                        count = int(values[cursor])
                        cursor += 1

                        if count < 0 or cursor + count > len(values):
                            raise ValueError("Invalid PLY list length.")

                        lists[name] = [
                            int(v) for v in values[cursor:cursor + count]
                        ]
                        cursor += count

                self._store_record(
                    element["name"], record, lists,
                    vertices, normals, colors, faces
                )

    def _read_binary_data(self, file, vertices, normals, colors, faces):
        endian = "<" if self.format == "binary_little_endian" else ">"

        for element in self.elements:
            for _ in range(element["count"]):
                record = {}
                lists = {}

                for prop in element["properties"]:
                    name = prop["name"]

                    if prop["kind"] == "scalar":
                        record[name] = self._read_scalar(
                            file, prop["type"], endian
                        )
                    else:
                        count = int(self._read_scalar(
                            file, prop["count_type"], endian
                        ))

                        if count < 0:
                            raise ValueError("Invalid negative PLY list length.")

                        lists[name] = [
                            int(self._read_scalar(file, prop["item_type"], endian))
                            for _ in range(count)
                        ]

                self._store_record(
                    element["name"], record, lists,
                    vertices, normals, colors, faces
                )

    @classmethod
    def _read_scalar(cls, file, type_name, endian):
        fmt, size = cls.TYPE_MAP[type_name]
        data = file.read(size)

        if len(data) != size:
            raise ValueError("Unexpected end of binary PLY data.")

        return struct.unpack(endian + fmt, data)[0]

    @staticmethod
    def _store_record(
        element_name, record, lists,
        vertices, normals, colors, faces
    ):
        if element_name == "vertex":
            vertices.append([
                record["x"], record["y"], record["z"]
            ])

            if all(k in record for k in ("nx", "ny", "nz")):
                normals.append([record["nx"], record["ny"], record["nz"]])

            color_keys = ("red", "green", "blue")
            if all(k in record for k in color_keys):
                colors.append([
                    PLYLoader._normalize_color(record[k])
                    for k in color_keys
                ])

        elif element_name == "face":
            face = lists.get("vertex_indices")
            if face is None:
                face = lists.get("vertex_index")

            if face is not None:
                faces.append(face)

    @staticmethod
    def _normalize_color(value):
        # Common PLY convention: integer RGB values in the range 0–255.
        if value > 1.0:
            return value / 255.0
        return value

    @staticmethod
    def _compute_normals(vertices, indices):
        normals = np.zeros_like(vertices)

        for i in range(0, len(indices), 3):
            i0, i1, i2 = indices[i:i + 3]

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


def load_ply(filename, shading="phong"):
    from core.mesh import Mesh

    loader = PLYLoader(filename)
    vertices, normals, colors, indices = loader.load()

    return Mesh(
        vertices=vertices,
        normals=normals,
        colors=colors,
        indices=indices,
        shading=shading,
    )
