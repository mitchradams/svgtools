# svgtools
## Revolve About Axis
### Description
Takes a 2D SVG profile and generates a set of laser-cuttable flat panels that interlock to form a revolved solid. The number of panels equals the number of faces; interlocking slots are computed automatically from the material thickness.
 
### To Run
```
pip install -r requirements.txt
python3 construct_3d/revolve_about_axis.py
```
 
### Current Assumptions
- Input file contains exactly one path
- The number of faces is a power of 2
- The axis of rotation is the center of the SVG path