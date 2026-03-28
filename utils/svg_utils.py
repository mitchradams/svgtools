#!/usr/bin/env python3

from svgpathtools import svg2paths2, Path, wsvg, Line, Arc

def load_svg_paths_from_file(filename : str):
    # Load and parse SVG paths from file
    paths, attributes, svg_attributes = svg2paths2(filename)
    return paths, [attributes, svg_attributes]

def save_svg_paths_to_file(paths, filename, attributes=None):
    #wsvg(paths, attributes=attributes, svg_attributes=svg_attributes, filename=filename)
    if attributes:
        wsvg(paths, attributes=attributes[0], svg_attributes=attributes[1], filename=filename)
    else:
        wsvg(paths, filename=filename)

def svg_path_to_polygon(svg_path : Path):
    # Convert svg_path to a list of points
    points = []
    for segment in svg_path:
        if isinstance(segment, Line):
            if hasattr(segment, 'start'):
                points.append((segment.start.real, segment.start.imag))
        if isinstance(segment, Arc): # todo: find a better way to handle arcs. We lose arc info, resulting in arcs becoming "choppy"
            RESOLUTION = 0.1 #todo: parameterize
            num_pts = int(segment.length() / RESOLUTION)
            if num_pts < 2:
                num_pts = 2
            t_values = [x / (num_pts - 1) for x in range(0, num_pts)]
            tpoints = [segment.point(t) for t in t_values]
            points += [(p.real, p.imag) for p in tpoints]
    if points[0] != points[-1]:
        points.append(points[0])
    return points

def polygon_to_svg_path(polygon):
    if polygon[0] != polygon[-1]:
        polygon.append(polygon[0])
    # Create a list of Line segments connecting each point
    segments = [Line(start=complex(polygon[i][0], polygon[i][1]), 
                     end=complex(polygon[i+1][0], polygon[i+1][1]))
                for i in range(len(polygon) - 1)]
    # Return a Path object containing these segments
    return Path(*segments)

def path_width(path : Path):
    return path_max_x(path) - path_min_x(path)

def path_height(path: Path):
    return path_max_y(path) - path_min_y(path)

def path_min_x(path: Path):
    return path.bbox()[0]

def path_max_x(path: Path):
    return path.bbox()[1]

def path_min_y(path: Path):
    return path.bbox()[2]

def path_max_y(path: Path):
    return path.bbox()[3]

def paths_width(paths : list[Path]):
    return paths_max_x(paths) - paths_min_x(paths)

def paths_height(paths : list[Path]):
    return paths_max_y(paths) - paths_min_y(paths)

def paths_min_x(paths : list[Path]):
    path_min_xs = [path_min_x(path) for path in paths]
    return min(path_min_xs)

def paths_max_x(paths : list[Path]):
    path_max_xs = [path_max_x(path) for path in paths]
    return max(path_max_xs)

def paths_min_y(paths : list[Path]):
    path_min_ys = [path_min_y(path) for path in paths]
    return min(path_min_ys)

def paths_max_y(paths : list[Path]):
    path_max_ys = [path_max_y(path) for path in paths]
    return max(path_max_ys)

# lays out groups of paths in a linear distribution
def distribute_svg_path_group_layout(path_groups : list[list[Path]], space_between_each) -> list[list[Path]]:
    distributed_paths = []
    if not path_groups:
        return distributed_paths
    for path_group in path_groups:
        if path_group:
            current_x = paths_min_x(path_group) # start at xmin of first path
            y = paths_min_y(path_group) # align all with ymin of first path
            break
    for path_group in path_groups:
        if path_group:
            translation = complex(current_x-paths_min_x(path_group), y-paths_min_y(path_group))
            translated_path_group = [path.translated(translation) for path in path_group]
            distributed_paths.append(translated_path_group)
            current_x = current_x + paths_width(path_group) + space_between_each
    return distributed_paths