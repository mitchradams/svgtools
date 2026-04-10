# svgtools

## Revolve About Axis

### Description

Takes a 2D SVG profile and generates a set of laser-cuttable flat panels that interlock to form a revolved solid. The number of panels equals the number of faces; interlocking slots are computed automatically from the material thickness.

### To Run

#### Install dependencies:

<details>
<summary>Linux/macOS</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

</details>

<details>
<summary>Windows</summary>

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

</details>

#### Run with GUI

```
python3 construct_3d/revolve_gui.py
```

To run the GUI with a live preview:
```
python3 construct_3d/revolve_gui.py --show-preview
```
To run with a live preview, you will need the libraries Pillow and cairosvg installed in your environment. Note that cairosvg might require additional tools for installation depending on your OS. See their [installation guide](https://cairosvg.org/documentation/#installation) for more details.

#### Run from the command line

```
python3 construct_3d/revolve_about_axis.py input.svg output.svg --faces 4 --thickness 3.175 --buffer 0.1 --max_width 400
```

Replace `input.svg` and `output.svg` with the input and output files, and replace, `4`, `3.175`, `0.1`, and `400` with the appropriate values for the number of cutouts to rotate (must be a factor of two), the thickness of the material, the extra thickness you would like to cut out of the material, and the maximum width the output layout should occupy before extending to a new row (or omit this parameter for no limit).

Run the following for the most up to date arguments and descriptions:
```
python3 construct_3d/revolve_about_axis.py -h
```

### Current Assumptions

- Input file contains exactly one path
- The number of faces is a power of 2
- The axis of rotation is the center of the SVG path

### Compile into an executable

Prerequisite: pyinstaller

<details>
<summary>Windows</summary>

```bat
pyinstaller --noconsole --icon assets/revolve.ico --name "Laser Symmetry" --paths construct_3d --paths geometric_operations --paths utils construct_3d/revolve_gui.py
```

</details>

<details>
<summary>Linux</summary>

```bash
pyinstaller --windowed --icon assets/revolve.png --name "Laser Symmetry" --paths construct_3d --paths geometric_operations --paths utils construct_3d/revolve_gui.py
```

</details>

<details>
<summary>macOS</summary>

```bash
pyinstaller --windowed --icon assets/revolve.icns --name "Laser Symmetry" --paths construct_3d --paths geometric_operations --paths utils construct_3d/revolve_gui.py
```

</details>
