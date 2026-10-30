# 3D Geometry Lab

Interactive PyOpenGL application for 2D/3D Object Rendering and Visualization of Atoms and Molecules.

## Setup

The project uses Python 3.12, GLFW, PyOpenGL, NumPy, OpenCV, Pillow, and Tkinter. On Windows, install Python 3.12 and the dependencies:

```bash
pip install -r requirements.txt
```

If using Conda, the supplied `environment.yml` can be used to recreate the environment:

```bash
conda env create -f environment.yml
conda activate computer-graphics-object-rendering
pip install -r requirements.txt
```

Run the application from the application root:

```bash
cd drawing-basic-shapes
python main.py
```

A desktop session with OpenGL 3.3 Core support is required. The application cannot render in a headless terminal without an OpenGL context/display.

## Feature — Basic shapes

The left panel can add 2D shapes (Triangle, Rectangle, Pentagon, Hexagon, Circle, Ellipse, Trapezoid, Star, Arrow) and 3D shapes (Cube, Sphere, Cylinder, Cone, Truncated Cone, Tetrahedron, Torus, Prism, and a user-defined surface `z = f(x, y)`). OBJ and PLY models can also be imported.

- Select an object by clicking its name in the **Objects** list.
- Use the **Transform** buttons to translate, rotate, scale, or reset the selected object.
- Drag with the left mouse button outside the GUI to rotate the camera; drag with the right mouse button to pan; use the scroll wheel to zoom.
- Press `W` to cycle through wireframe, points, and filled polygon rendering.
- Shape shading shortcuts: `F` Flat, `G` Gouraud, `P` Phong, `I` interpolated vertex color, and `T` texture (for shapes with texture coordinates).
- Press `H` to toggle the help overlay, `Tab` to select the next object, `Delete` to delete the selected object, and `Q`/`Esc` to quit. Press `R` (or use the GUI control) to toggle the world grid; `G` remains the Gouraud shading shortcut.

The default texture image is `drawing-basic-shapes/assets/checker.png`. Press `T` after selecting an object to apply it. Texture mapping is enabled for all built-in 2D and 3D shapes, plus imported OBJ/PLY meshes. Shapes with explicit UV layouts (such as the cube, sphere, cylinder, cone, and truncated cone) use those layouts; other shapes use a normalized planar projection, which is a practical fallback rather than a hand-authored UV unwrap.

## Feature — Atoms and molecules

Use the **Part 2: Atoms & Molecules** buttons in the left panel:

- **Bohr H**, **Bohr C**, **Bohr O**: add simplified Bohr-style models of hydrogen, carbon, and oxygen. Electrons are distributed over the first two shells (up to two electrons in the first shell); the nucleus is represented as one simplified sphere.
- **Molecule H2O**: adds a water ball-and-stick model with one red oxygen sphere, two white hydrogen spheres, and connecting cylinders.
- **Molecule CO2**: adds a linear carbon dioxide model with a dark carbon sphere, two red oxygen spheres, and connecting cylinders.
- **Toggle Orbit** or press `E`: pause/resume electron motion for the selected Bohr atom.
- Select an atom or molecule in the Objects list and use the existing Transform controls to change its position, orientation, or scale. Camera rotation, pan, and zoom are shared with Part 1.

These are schematic visualization models intended for the assignment, not scientifically scaled atomic or molecular structures. Bond lengths, sphere sizes, and shell radii are illustrative.

## Project structure

```text
computer-graphics-object-rendering/
│
├── drawing-basic-shapes/
│   ├── main.py                 # Application entry point
│   │
│   ├── core/                   # Core shape and mesh abstractions,
│   │                           # shape factory, and color palette
│   │
│   ├── shapes/
│   │   ├── two_d/              # 2D geometric shapes
│   │   └── three_d/            # 3D geometric shapes and atomic models
│   │
│   ├── loaders/                # OBJ and PLY model loaders
│   │
│   ├── models/                 # Sample 3D models
│   │
│   ├── assets/                 # Textures and image assets
│   │
│   └── shaders/                # GLSL vertex and fragment shaders
│
├── cglibs/                     # OpenGL rendering, viewer, GUI,
│                               # camera, transformations, and utilities
│
├── environment.yml             # Conda environment configuration
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

## Notes

- Texture mapping requires UV coordinates. The application supplies UV coordinates for all built-in shapes; imported OBJ/PLY meshes without UVs receive a planar-projection fallback. This fallback can stretch the checker pattern on complex geometry.
- The Bohr model and molecule feature set is implemented in `drawing-basic-shapes/shapes/three_d/atomic_models.py` and integrated into the main GUI/viewer.


### User-provided textures

Select a regular shape or imported OBJ/PLY mesh, then click **Upload Texture** in the Import Model section and choose a PNG, JPG/JPEG, BMP, TGA, or TIFF image. The chosen image is applied immediately; the object switches to Texture shading. Press `T` to toggle Texture shading again later. For best results, use a square or seamless image. Shapes without authored UVs use planar UV mapping, so images may stretch on complex surfaces.


## Other interface features

- Toggleable world grid and XYZ axes; use the GUI's `GRID / XYZ` control or press `R`.
- New regular shapes receive varied neon gradients from `core/palette.py`.
- The grid is a world-space reference overlay and is drawn behind scene geometry.
- The Objects list has a fixed-height viewport and scrollbar. Use the mouse wheel while the pointer is over the list to browse objects.
- Use **COLOR / GRADIENT** to apply a solid color from the native color picker or a preset gradient from `core/palette.py` (`blue-cyan`, `blue-violet`, `cyan-violet`, `violet-pink`, `orange-gold`, `green-cyan`, `full-spectrum`). The selected object's vertex-color buffer is updated immediately.

## Cube panorama texture

For a cube, **Upload Texture** accepts a single equirectangular panorama (ideally a 2:1 width-to-height image). The image is projected to a standard 4-by-3 cube-cross atlas and sampled across the six faces, instead of repeating the same entire image independently on every face. Other shapes continue to use their own UV layout or planar-projection fallback.
