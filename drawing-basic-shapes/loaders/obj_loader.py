import numpy as np


class OBJLoader:
    """
    Minimal OBJ loader for Assignment 1.

    Supported:
        v
        vn
        f

    Face formats:
        v
        v/vt
        v//vn
        v/vt/vn

    Faces with more than 3 vertices are triangulated
    using a triangle fan.
    """

    def __init__(self, filename):
        self.filename = filename

        self.positions = []
        self.normals = []

        self.vertices = []
        self.vertex_normals = []
        self.indices = []

        # Maps an OBJ vertex specification
        # to a final vertex index.
        self.vertex_map = {}

    # =============================================================
    # Public API
    # =============================================================

    def load(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                command = parts[0]

                if command == 'v':
                    self._parse_vertex(parts)
                elif command == 'vn':
                    self._parse_normal(parts)
                elif command == 'f':
                    self._parse_face(parts[1:])

        vertices = np.asarray(self.vertices, dtype=np.float32)
        normals = np.asarray(self.vertex_normals, dtype=np.float32)
        indices = np.asarray(self.indices, dtype=np.uint32)

        # If the OBJ contains no normals,
        # calculate smooth vertex normals.
        if len(self.normals) == 0:
            normals = self._compute_normals(vertices, indices)

        return vertices, normals, indices

    # =============================================================
    # Parsing
    # =============================================================

    def _parse_vertex(self, parts):
        if len(parts) < 4:
            raise ValueError(
                f"Invalid vertex line in {self.filename}"
            )
        x = float(parts[1])
        y = float(parts[2])
        z = float(parts[3])
        self.positions.append([x, y, z])

    def _parse_normal(self, parts):
        if len(parts) < 4:
            raise ValueError(
                f"Invalid normal line in {self.filename}"
            )
        x = float(parts[1])
        y = float(parts[2])
        z = float(parts[3])
        self.normals.append([x, y, z])

    def _parse_face(self, face_tokens):
        if len(face_tokens) < 3:
            return

        face_indices = []

        for token in face_tokens:
            key = token

            if key not in self.vertex_map:
                position_index, normal_index = \
                    self._parse_face_vertex(token)

                position = self.positions[position_index]
                self.vertices.append(position)

                if normal_index is not None:
                    normal = self.normals[normal_index]
                else:
                    normal = [0.0, 0.0, 0.0]

                self.vertex_normals.append(normal)
                new_index = len(self.vertices) - 1
                self.vertex_map[key] = new_index

            face_indices.append(self.vertex_map[key])

        # Triangle fan:
        #
        # v0 v1 v2 v3
        #
        # becomes:
        #
        # v0 v1 v2
        # v0 v2 v3

        for i in range(1, len(face_indices) - 1):
            self.indices.extend([
                face_indices[0],
                face_indices[i],
                face_indices[i + 1]
            ])

    def _parse_face_vertex(self, token):
        parts = token.split('/')

        # Position index
        position_index = self._resolve_index(
            int(parts[0]),
            len(self.positions)
        )

        # Normal index
        normal_index = None

        if len(parts) >= 3 and parts[2] != '':
            normal_index = self._resolve_index(
                int(parts[2]),
                len(self.normals)
            )

        return position_index, normal_index

    @staticmethod
    def _resolve_index(index, size):
        """
        OBJ indices are 1-based.

        Positive:
            1 -> first element
            2 -> second element

        Negative:
            -1 -> last element
            -2 -> second last element
        """

        if index > 0:
            return index - 1

        return size + index

    # =============================================================
    # Normal generation
    # =============================================================

    def _compute_normals(self, vertices, indices):
        normals = np.zeros_like(vertices)

        for i in range(0, len(indices), 3):
            i0 = indices[i]
            i1 = indices[i + 1]
            i2 = indices[i + 2]

            a = vertices[i0]
            b = vertices[i1]
            c = vertices[i2]

            face_normal = np.cross(b - a, c - a)
            length = np.linalg.norm(face_normal)

            if length > 1e-8:
                face_normal /= length

            normals[i0] += face_normal
            normals[i1] += face_normal
            normals[i2] += face_normal

        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        lengths[lengths < 1e-8] = 1.0
        normals /= lengths

        return normals
    
def load_obj(filename, shading='phong'):
    from core.mesh import Mesh
    loader = OBJLoader(filename)
    vertices, normals, indices = loader.load()
    return Mesh(vertices=vertices, normals=normals, indices=indices, shading=shading)