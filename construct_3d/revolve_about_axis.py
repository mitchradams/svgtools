#!/usr/bin/env python3

import geometric_operations.difference as difference
import geometric_operations.union as union
from svgpathtools import Path
import utils.svg_utils as svg_utils
import utils.shapes as shapes
import math


def generate_masks(num_faces: int, bottom_y: float, top_y: float,
                   center_x: float, material_thickness: float,
                   buffer: float) -> list[Path]:
    if (num_faces <= 0) or (int(num_faces) & (int(num_faces - 1))) != 0:
        raise ValueError(f"Invalid number of faces: {num_faces}. Must be a power of 2.")

    mask_width = material_thickness / math.tan(math.pi / (2 * num_faces)) + buffer
    mask_height = buffer + (top_y - bottom_y) / 2
    mask_origin_x = center_x - mask_width / 2

    mask1 = shapes.rectangle(mask_width, mask_height,
                              [mask_origin_x, bottom_y - buffer / 2])
    mask2 = shapes.rectangle(mask_width, mask_height,
                              [mask_origin_x, bottom_y + mask_height - buffer / 2])

    if num_faces == 2:
        return [mask1, mask2]

    masks = []
    mid_y = bottom_y + (top_y - bottom_y) / 2
    for mask in generate_masks(num_faces // 2, mid_y, top_y,
                                center_x, material_thickness, buffer):
        masks.append(union.get_union_paths([mask1] + [mask]))
    for mask in generate_masks(num_faces // 2, bottom_y, mid_y,
                                center_x, material_thickness, buffer):
        masks.append(union.get_union_paths([mask2] + [mask]))
    return masks


def revolve_path_about_axis(path: Path, num_faces: int,
                             material_thickness: float,
                             buffer: float) -> list[list[Path]]:
    center_x = svg_utils.path_min_x(path) + svg_utils.path_width(path) / 2
    masks = generate_masks(num_faces,
                           svg_utils.path_min_y(path),
                           svg_utils.path_max_y(path),
                           center_x, material_thickness, buffer)
    return [difference.get_difference_paths(path, mask) for mask in masks]


def revolve_path_from_file_about_axis(filename: str, output_file: str,
                                       num_faces: int,
                                       material_thickness: float,
                                       buffer: float) -> list[list[Path]]:
    # load_svg_paths_from_file now returns paths already in mm + a metadata dict
    paths_from_file, metadata = svg_utils.load_svg_paths_from_file(filename)
    path_from_file = paths_from_file[0]  # currently assumes single path per file

    rotation_paths = revolve_path_about_axis(path_from_file, num_faces,
                                              material_thickness, buffer)
    distributed = svg_utils.distribute_svg_path_group_layout(rotation_paths,
                                                              material_thickness)

    # save_svg_paths_to_file handles the physical-unit header automatically
    svg_utils.save_svg_paths_to_file(sum(distributed, []), output_file,
                                     stroke_width_mm=0.1)
    return distributed


def test():
    test_svg_file = './construct_3d/test_files/test_1.svg'
    test_output_file = '3d_revolve_test_result.svg'
    # Units in mm
    revolve_path_from_file_about_axis(test_svg_file, test_output_file,
                                       4, 3.175, 1.0)


if __name__ == '__main__':
    test()