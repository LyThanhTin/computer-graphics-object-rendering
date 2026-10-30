"""Bohr-style atomic models and simple ball-and-stick molecules.

The wrapper shares one Sphere, one Cylinder, and one Torus mesh between all
components. Per-instance transforms and vertex colors are applied while drawing.
"""
from __future__ import annotations

import math
import time

import numpy as np
import OpenGL.GL as GL
import glfw

from cglibs import transform as T
from shapes.three_d.sphere import Sphere
from shapes.three_d.cylinder import Cylinder
from shapes.three_d.torus import Torus
from core.palette import CYAN, BLUE, INDIGO, VIOLET, MAGENTA, PINK, ORANGE, GOLD, GREEN


ELEMENTS = {
    "H": {"name": "Hydrogen", "atomic_number": 1, "color": VIOLET},
    "C": {"name": "Carbon", "atomic_number": 6, "color": GOLD},
    "O": {"name": "Oxygen", "atomic_number": 8, "color": PINK},
}

ELECTRON_COLOR = (0.12, 0.62, 1.0)
ORBIT_COLOR = (0.18, 0.42, 0.62)
BOND_COLOR = (0.72, 0.76, 0.82)


def _translation(position):
    return T.translate(float(position[0]), float(position[1]), float(position[2]))


def _scale3(scale):
    return T.scale(float(scale[0]), float(scale[1]), float(scale[2]))


def _bond_transform(start, end, radius=0.055):
    """Transform a unit-height Y-axis cylinder to the segment start -> end."""
    start = np.asarray(start, dtype=np.float32)
    end = np.asarray(end, dtype=np.float32)
    direction = end - start
    length = float(np.linalg.norm(direction))
    if length < 1e-8:
        return T.identity()

    direction /= length
    y_axis = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    axis = np.cross(y_axis, direction)
    dot = float(np.clip(np.dot(y_axis, direction), -1.0, 1.0))
    angle = math.degrees(math.acos(dot))

    if np.linalg.norm(axis) < 1e-8:
        rotation = T.identity() if dot > 0 else T.rotate((1.0, 0.0, 0.0), 180.0)
    else:
        rotation = T.rotate(axis, angle)

    center = (start + end) * 0.5
    # Default Cylinder has radius 0.5 and height 1.0.
    return _translation(center) @ rotation @ _scale3((radius * 2.0, length, radius * 2.0))


class AtomicModel:
    """One selectable Bohr atom or ball-and-stick molecule."""

    # Keep one GPU mesh per primitive for all atomic objects. This avoids
    # recompiling a full shader set every time another atom/molecule is added.
    _shared_meshes = None

    def __init__(self, mode="bohr", element="H", molecule=None):
        self.mode = mode
        self.element = element
        self.molecule = molecule
        self.model = T.identity()
        self.animate_orbits = True
        self._animation_elapsed = 0.0
        self._last_tick = time.perf_counter()

        # Meshes are shared across all atomic models.
        if AtomicModel._shared_meshes is None:
            AtomicModel._shared_meshes = {
                "sphere": Sphere(radius=0.5, segments=20, rings=12, shading="phong"),
                "cylinder": Cylinder(radius=0.5, height=1.0, segments=16, shading="phong"),
                "torus": Torus(major_radius=1.0, minor_radius=0.035,
                               major_segments=48, minor_segments=8, shading="phong"),
            }
        self._sphere = AtomicModel._shared_meshes["sphere"]
        self._cylinder = AtomicModel._shared_meshes["cylinder"]
        self._torus = AtomicModel._shared_meshes["torus"]

        self._atoms = []
        self._bonds = []
        self._orbits = []
        self.display_name = ""

        if mode == "bohr":
            self._build_bohr_atom(element)
        elif mode == "molecule":
            self._build_molecule(molecule)
        else:
            raise ValueError(f"Unsupported atomic model mode: {mode}")

    def _build_bohr_atom(self, element):
        if element not in ELEMENTS:
            raise ValueError(f"Unsupported element: {element}")

        info = ELEMENTS[element]
        self.display_name = f"Bohr {info['name']}"
        # The nucleus is a simplified single sphere, not a proton/neutron model.
        self._atoms.append({
            "position": np.array([0.0, 0.0, 0.0], dtype=np.float32),
            "scale": (0.22, 0.22, 0.22),
            "color": info["color"],
        })

        atomic_number = info["atomic_number"]
        shell_counts = [min(atomic_number, 2), max(0, atomic_number - 2)]
        shell_radii = [0.43, 0.72]
        shell_tilts = [T.identity(), T.rotate((1.0, 0.0, 0.0), 58.0)]
        electron_index = 0

        for shell_index, count in enumerate(shell_counts):
            if count <= 0:
                continue
            radius = shell_radii[shell_index]
            self._orbits.append({"radius": radius, "rotation": shell_tilts[shell_index]})
            for index in range(count):
                self._atoms.append({
                    "electron": True,
                    "shell_radius": radius,
                    "angle_offset": 2.0 * math.pi * index / count + 0.35 * shell_index,
                    "angular_speed": 0.9 + 0.25 * shell_index + 0.08 * electron_index,
                    "rotation": shell_tilts[shell_index],
                    "scale": (0.085, 0.085, 0.085),
                    "color": ELECTRON_COLOR,
                })
                electron_index += 1

    def _build_molecule(self, molecule):
        if molecule == "H2O":
            self.display_name = "Molecule H2O"
            # Oxygen at the origin; two hydrogen atoms form an approximate 104.5-degree angle.
            atoms = [
                # Slightly separated spheres leave a clearly visible bond segment.
                # The H-O-H angle is approximately 104.5 degrees.
                ("O", (0.0, 0.0, 0.0), 0.24),
                ("H", (-0.50, 0.387, 0.0), 0.16),
                ("H", (0.50, 0.387, 0.0), 0.16),
            ]
            bond_pairs = [(0, 1), (0, 2)]
        elif molecule == "CO2":
            self.display_name = "Molecule CO2"
            atoms = [
                ("O", (-0.88, 0.0, 0.0), 0.27),
                ("C", (0.0, 0.0, 0.0), 0.25),
                ("O", (0.88, 0.0, 0.0), 0.27),
            ]
            bond_pairs = [(0, 1), (1, 2)]
        else:
            raise ValueError(f"Unsupported molecule: {molecule}")

        positions = []
        atom_radii = []
        for symbol, position, radius in atoms:
            position = np.asarray(position, dtype=np.float32)
            positions.append(position)
            atom_radii.append(radius)
            self._atoms.append({
                "position": position,
                "scale": (radius * 2.0, radius * 2.0, radius * 2.0),
                "color": ELEMENTS[symbol]["color"],
            })

        for start_index, end_index in bond_pairs:
            start = positions[start_index]
            end = positions[end_index]
            direction = end - start
            distance = float(np.linalg.norm(direction))
            if distance < 1e-8:
                continue
            direction /= distance
            # End the cylinder just inside each sphere so it joins both atoms
            # without being completely hidden inside overlapping spheres.
            inset = min(atom_radii[start_index] * 0.82,
                        atom_radii[end_index] * 0.82,
                        distance * 0.20)
            bond_start = start + direction * inset
            bond_end = end - direction * inset
            self._bonds.append({
                "transform": _bond_transform(bond_start, bond_end),
                "color": BOND_COLOR,
            })

    def _set_mesh_color(self, mesh, color):
        """Update the shared mesh's vertex-color VBO for the next draw call."""
        values = np.tile(np.asarray(color, dtype=np.float32), (mesh.vertex_count, 1))
        buffer_id = mesh.vao.vbo.get(1)
        if buffer_id is None:
            return
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, buffer_id)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, values.nbytes, values, GL.GL_DYNAMIC_DRAW)

    def _draw_mesh(self, mesh, projection, view, local_transform, color):
        self._set_mesh_color(mesh, color)
        mesh.draw(projection, view @ self.model @ local_transform, None)

    def draw(self, projection, view, model=None):
        if self.mode == "bohr":
            now = time.perf_counter()
            delta = now - self._last_tick
            self._last_tick = now
            if self.animate_orbits:
                self._animation_elapsed += delta
            elapsed = self._animation_elapsed
            for orbit in self._orbits:
                local = orbit["rotation"] @ T.scale(orbit["radius"])
                self._draw_mesh(self._torus, projection, view, local, ORBIT_COLOR)

            for atom in self._atoms:
                if atom.get("electron"):
                    angle = atom["angle_offset"]
                    if self.animate_orbits:
                        angle += elapsed * atom["angular_speed"]
                    radius = atom["shell_radius"]
                    point = np.array([radius * math.cos(angle), 0.0,
                                      radius * math.sin(angle), 1.0], dtype=np.float32)
                    point = atom["rotation"] @ point
                    position = point[:3]
                else:
                    position = atom["position"]
                local = _translation(position) @ _scale3(atom["scale"])
                self._draw_mesh(self._sphere, projection, view, local, atom["color"])
        else:
            # Draw bonds first so their ends tuck into the atom spheres.
            for bond in self._bonds:
                self._draw_mesh(self._cylinder, projection, view,
                                bond["transform"], bond["color"])
            for atom in self._atoms:
                local = _translation(atom["position"]) @ _scale3(atom["scale"])
                self._draw_mesh(self._sphere, projection, view, local, atom["color"])

    # Transform hooks used by Viewer GUI controls.
    def translate(self, x=0.0, y=0.0, z=0.0):
        self.model = self.model @ T.translate(x, y, z)

    def scale(self, x, y=None, z=None):
        self.model = self.model @ T.scale(x, y, z)

    def rotate(self, axis=(0.0, 1.0, 0.0), angle=0.0):
        self.model = self.model @ T.rotate(axis, angle)

    def reset_transform(self):
        self.model = T.identity()

    def toggle_animation(self):
        if self.mode == "bohr":
            self._last_tick = time.perf_counter()
            self.animate_orbits = not self.animate_orbits

    def key_handler(self, key):
        if key == glfw.KEY_E:
            self.toggle_animation()
        elif key == glfw.KEY_R:
            self.reset_transform()
