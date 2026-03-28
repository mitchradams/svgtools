#!/usr/bin/env python3

from svgpathtools import Path
import pyclipper
import utils.svg_utils as svg_utils


def get_union_paths(paths: list[Path]) -> list[Path]:
    polygons = [svg_utils.svg_path_to_polygon(p) for p in paths]

    SCALE = pyclipper.scale_to_clipper(1)
    scaled = [pyclipper.scale_to_clipper(p, SCALE) for p in polygons]

    pc = pyclipper.Pyclipper()
    union_polys = [scaled[0]]
    for poly in scaled[1:]:
        pc.Clear()
        for subj in union_polys:
            pc.AddPath(subj, pyclipper.PT_SUBJECT, True)
        pc.AddPath(poly, pyclipper.PT_CLIP, True)
        union_polys = pc.Execute(pyclipper.CT_UNION)

    unscaled = [pyclipper.scale_from_clipper(p, SCALE) for p in union_polys]
    return [svg_utils.polygon_to_svg_path(p) for p in unscaled]


def get_union_path_from_files(svg_files: list[str], output_file: str):
    all_paths: list[Path] = []
    for f in svg_files:
        paths, _ = svg_utils.load_svg_paths_from_file(f)
        all_paths.extend(paths)

    union_paths = get_union_paths(all_paths)

    if union_paths:
        svg_utils.save_svg_paths_to_file(union_paths, output_file)
    else:
        print("No union found between the paths.")


def test():
    svg_files = [
        './geometric_operations/test_files/test_1.svg',
        './geometric_operations/test_files/test_2.svg',
        './geometric_operations/test_files/test_3.svg',
        './geometric_operations/test_files/test_4.svg',
    ]
    get_union_path_from_files(svg_files, 'union_test_result.svg')


if __name__ == '__main__':
    test()