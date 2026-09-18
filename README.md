## Setup

Conda env **computer-graphics-object-rendering** (Python 3.12). Windows, Linux, or macOS with a display and OpenGL 3.3:

```bash
conda activate computer-graphics-object-rendering
```

Recreate if needed (from this folder):

```bash
conda env create -f environment.yml
conda activate computer-graphics-object-rendering
pip install -r requirements.txt
```

Needs a display. Samples request OpenGL 3.3 Core + forward compatible.