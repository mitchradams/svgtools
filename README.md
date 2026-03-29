# svgtools
## Revolve About Axis
### Description
Takes a 2D SVG profile and generates a set of laser-cuttable flat panels that interlock to form a revolved solid. The number of panels equals the number of faces; interlocking slots are computed automatically from the material thickness.
 
### To Run
#### Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### Run with GUI
```
python3 construct_3d/revolve_gui.py
```

#### Run from command line
```
python3 construct_3d/revolve_about_axis.py input.svg output.svg --faces 4 --thickness 3.175 --buffer 0.1
```
(Replace `input.svg` and `output.svg` with the input and output files, and replace, `4`, `3.175`, and `0.1` with the appropriate values for the number of cutouts to rotate, the thickness of the material, and the extra thickness you would like to cut out of the material.)
 
### Current Assumptions
- Input file contains exactly one path
- The number of faces is a power of 2
- The axis of rotation is the center of the SVG path