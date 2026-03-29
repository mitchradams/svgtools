#!/usr/bin/env python3

from svgpathtools import Path
import pyclipper
import utils.svg_utils as svg_utils


def get_difference_paths(subject_path: Path,
                         clip_paths: list[Path]) -> list[Path]:
    subj_poly = svg_utils.svg_path_to_polygon(subject_path)
    clip_polys = [svg_utils.svg_path_to_polygon(p) for p in clip_paths]

    # pyclipper requires integer coordinates; multiply by a fixed scale factor
    # to preserve sub-mm precision before rounding to int.
    SCALE = 1000
    subj_scaled = pyclipper.scale_to_clipper(subj_poly, SCALE)
    clips_scaled = [pyclipper.scale_to_clipper(p, SCALE) for p in clip_polys]

    pc = pyclipper.Pyclipper()
    difference_polys = [subj_scaled]
    for clip in clips_scaled:
        pc.Clear()
        for subj in difference_polys:
            pc.AddPath(subj, pyclipper.PT_SUBJECT, True)
        pc.AddPath(clip, pyclipper.PT_CLIP, True)
        difference_polys = pc.Execute(pyclipper.CT_DIFFERENCE)

    unscaled = [pyclipper.scale_from_clipper(p, SCALE) for p in difference_polys]
    return [svg_utils.polygon_to_svg_path(p) for p in unscaled]


def get_difference_paths_from_files(subject_svg_file: str,
                                     clip_svg_files: list[str],
                                     output_file: str):
    subject_paths, _ = svg_utils.load_svg_paths_from_file(subject_svg_file)

    clip_paths: list[Path] = []
    for f in clip_svg_files:
        paths, _ = svg_utils.load_svg_paths_from_file(f)
        clip_paths.extend(paths)

    difference_paths: list[Path] = []
    for subj in subject_paths:
        difference_paths.extend(get_difference_paths(subj, clip_paths))

    if difference_paths:
        svg_utils.save_svg_paths_to_file(difference_paths, output_file)
    else:
        print("No difference found between the paths.")


def test():
    subject_svg_file = './geometric_operations/test_files/test_1.svg'
    clip_svg_files = [
        './geometric_operations/test_files/test_2.svg',
        './geometric_operations/test_files/test_3.svg',
        './geometric_operations/test_files/test_4.svg',
    ]
    get_difference_paths_from_files(subject_svg_file, clip_svg_files,
                                    'difference_test_result.svg')


if __name__ == '__main__':
    test()