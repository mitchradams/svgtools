#!/usr/bin/env python3
 
import geometric_operations.difference as difference
from svgpathtools import Path
import utils.svg_utils as svg_utils
import utils.shapes as shapes
import math
 
 
def generate_masks(num_faces: int, bottom_y: float, top_y: float,
                   center_x: float, material_thickness: float,
                   buffer: float) -> list[list[Path]]:
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
        return [[mask1], [mask2]]
 
    masks = []
    mid_y = bottom_y + (top_y - bottom_y) / 2
    for sub_masks in generate_masks(num_faces // 2, mid_y, top_y,
                                    center_x, material_thickness, buffer):
        masks.append([mask1] + sub_masks)
    for sub_masks in generate_masks(num_faces // 2, bottom_y, mid_y,
                                    center_x, material_thickness, buffer):
        masks.append([mask2] + sub_masks)
    return masks
 
 
def revolve_path_about_axis(path: Path, num_faces: int,
                             material_thickness: float,
                             buffer: float) -> list[list[Path]]:
    center_x = svg_utils.path_min_x(path) + svg_utils.path_width(path) / 2
    mask_lists = generate_masks(num_faces,
                                svg_utils.path_min_y(path),
                                svg_utils.path_max_y(path),
                                center_x, material_thickness, buffer)
    return [difference.get_difference_paths(path, mask_list)
            for mask_list in mask_lists]
 
 
def revolve_path_from_file_about_axis(filename: str, output_file: str,
                                       num_faces: int,
                                       material_thickness: float,
                                       buffer: float) -> list[list[Path]]:
    paths_from_file, metadata = svg_utils.load_svg_paths_from_file(filename)
    path_from_file = paths_from_file[0]  # currently assumes single path per file
 
    rotation_paths = revolve_path_about_axis(path_from_file, num_faces,
                                              material_thickness, buffer)
    distributed = svg_utils.distribute_svg_path_group_layout(rotation_paths,
                                                              material_thickness)
    svg_utils.save_svg_paths_to_file(sum(distributed, []), output_file,
                                     stroke_width_mm=0.1)
    return distributed

def test():
    test_svg_file = './construct_3d/test_files/test_1.svg'
    test_output_file = '3d_revolve_test_result.svg'
    # Units in mm
    revolve_path_from_file_about_axis(test_svg_file, test_output_file,
                                       4, 3.175, 1.0)

import argparse

def main():
    parser = argparse.ArgumentParser(description='Revolve SVG path about axis to create faces for 3D construction.')
    parser.add_argument('input_svg', help='Input SVG file path')
    parser.add_argument('output_svg', help='Output SVG file path')
    parser.add_argument('--faces', type=int, choices=[2,4,8,16,32,64], required=True, help='Number of faces (must be 2, 4, 8, 16, 32, or 64)')
    parser.add_argument('--thickness', type=float, required=True, help='Material thickness in mm')
    parser.add_argument('--buffer', type=float, required=True, help='Buffer size in mm')

    args = parser.parse_args()

    try:
        revolve_path_from_file_about_axis(
            args.input_svg,
            args.output_svg,
            args.faces,
            args.thickness,
            args.buffer
        )
        print(f"Output saved to {args.output_svg}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        sys.argv.remove('--test')
        test()
    else:
        main()