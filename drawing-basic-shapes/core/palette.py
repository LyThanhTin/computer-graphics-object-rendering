import numpy as np


# Cyber Spectrum Palette
CYAN = [0.05, 0.95, 1.00]
BLUE = [0.12, 0.32, 1.00]
INDIGO = [0.30, 0.20, 0.90]
VIOLET = [0.58, 0.16, 1.00]
MAGENTA = [1.00, 0.08, 0.72]
PINK = [1.00, 0.25, 0.55]
ORANGE = [1.00, 0.45, 0.05]
GOLD = [1.00, 0.80, 0.10]
GREEN = [0.15, 1.00, 0.40]


# Preset gradients
CYBER_BLUE_CYAN = [
    BLUE,
    CYAN,
]

CYBER_BLUE_VIOLET = [
    BLUE,
    INDIGO,
    VIOLET,
]

CYBER_CYAN_VIOLET = [
    CYAN,
    BLUE,
    VIOLET,
]

CYBER_VIOLET_PINK = [
    VIOLET,
    MAGENTA,
    PINK,
]

CYBER_ORANGE_GOLD = [
    ORANGE,
    GOLD,
]

CYBER_GREEN_CYAN = [
    GREEN,
    CYAN,
]

CYBER_FULL_SPECTRUM = [
    CYAN,
    BLUE,
    INDIGO,
    VIOLET,
    MAGENTA,
    PINK,
    ORANGE,
    GOLD,
    GREEN,
]


# Color generation helpers
def create_gradient_colors(count, palette):
    """
    Create interpolated colors across the given palette.

    Parameters
    ----------
    count : int
        Number of colors to generate.

    palette : list
        List of RGB colors.

    Returns
    -------
    np.ndarray
        Array with shape (count, 3).
    """

    if count <= 0:
        return np.empty((0, 3), dtype=np.float32)

    palette = np.asarray(palette, dtype=np.float32)

    if len(palette) == 1:
        return np.tile(palette[0], (count, 1))

    positions = np.linspace(0, len(palette) - 1, count)

    colors = []

    for position in positions:
        left = int(np.floor(position))
        right = min(left + 1, len(palette) - 1)
        t = position - left
        color = ((1.0 - t) * palette[left] + t * palette[right])
        colors.append(color)

    return np.array(colors, dtype=np.float32)


def create_cyclic_colors(count, palette):
    """
    Assign palette colors cyclically.
    """

    if count <= 0:
        return np.empty((0, 3), dtype=np.float32)

    palette = np.asarray(palette, dtype=np.float32)

    return np.array(
        [palette[i % len(palette)] for i in range(count)],
        dtype=np.float32
    )

def create_face_colors(face_count, vertices_per_face, palette):
    face_colors = create_cyclic_colors(face_count, palette)

    return np.repeat(face_colors, vertices_per_face, axis=0)