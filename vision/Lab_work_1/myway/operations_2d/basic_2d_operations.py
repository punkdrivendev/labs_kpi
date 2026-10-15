import numpy as np

def check_points(points):
    if not isinstance(points, np.ndarray):
        raise TypeError("Points must be a numpy array")

    if points.shape != (3, 3):
        raise ValueError("Triangle points must be a 3x3 matrix")

    if not np.allclose(points[2], [1, 1, 1]):
        raise ValueError("Last row must contain homogeneous coordinates [1, 1, 1]")

def move_2d(points, dx, dy):
    check_points(points)

    translation_matrix = np.array([
        [1, 0, dx],
        [0, 1, dy],
        [0, 0, 1]
    ], dtype=float)

    return translation_matrix @ points

def rotate_2d(points, degrees):
    check_points(points)

    angle = np.radians(degrees)

    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle),  np.cos(angle), 0],
        [0,              0,             1]
    ])

    return rotation_matrix @ points

def scale_figure(points, scale):
    check_points(points)

    scale_matrix = np.array([
        [scale, 0,     0],
        [0,     scale, 0],
        [0,     0,     1]
    ])

    return scale_matrix @ points

def rotate_scale_2d(points, degrees, scale):
    check_points(points)

    angle = np.radians(degrees)

    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle),  np.cos(angle), 0],
        [0,              0,             1]
    ])

    scale_matrix = np.array([
        [scale, 0,     0],
        [0,     scale, 0],
        [0,     0,     1]
    ])

    combined_matrix = rotation_matrix @ scale_matrix

    return combined_matrix @ points

def inside_window(points, x_min, x_max, y_min, y_max):
    check_points(points)

    x = points[0]
    y = points[1]

    return (
        np.all(x >= x_min)
        and np.all(x <= x_max)
        and np.all(y >= y_min)
        and np.all(y <= y_max)
    )
