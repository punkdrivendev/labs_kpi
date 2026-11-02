import numpy as np

def check_points(points):
    if not isinstance(points, np.ndarray):
        raise TypeError("Points must be a numpy array")

    if points.ndim != 2 or points.shape[0] != 4:
        raise ValueError("3D points must be a 4xN homogeneous matrix")

    if not np.allclose(points[3], 1):
        raise ValueError("The last row must contain homogeneous coordinates equal to 1")


def make_triangular_pyramid(size=2.0):
    """
    Matrix format:
    [x1 x2 x3 x4]
    [y1 y2 y3 y4]
    [z1 z2 z3 z4]
    [1  1  1  1 ]
    """
    s = float(size)

    return np.array([
        [-s,  s,  0.0, 0.0],
        [-s / 2, -s / 2, s, 0.0],
        [0.0, 0.0, 0.0, 1.5 * s],
        [1.0, 1.0, 1.0, 1.0],
    ], dtype=float)


def rotation_x_matrix(degrees):
    angle = np.radians(degrees)
    c = np.cos(angle)
    s = np.sin(angle)

    return np.array([
        [1, 0,  0, 0],
        [0, c, -s, 0],
        [0, s,  c, 0],
        [0, 0,  0, 1],
    ], dtype=float)


def rotation_y_matrix(degrees):
    angle = np.radians(degrees)
    c = np.cos(angle)
    s = np.sin(angle)

    return np.array([
        [ c, 0, s, 0],
        [ 0, 1, 0, 0],
        [-s, 0, c, 0],
        [ 0, 0, 0, 1],
    ], dtype=float)


def rotation_z_matrix(degrees):
    angle = np.radians(degrees)
    c = np.cos(angle)
    s = np.sin(angle)

    return np.array([
        [c, -s, 0, 0],
        [s,  c, 0, 0],
        [0,  0, 1, 0],
        [0,  0, 0, 1],
    ], dtype=float)


def rotate_3d(points, degrees, axis="z"):
    check_points(points)

    if axis == "x":
        matrix = rotation_x_matrix(degrees)
    elif axis == "y":
        matrix = rotation_y_matrix(degrees)
    elif axis == "z":
        matrix = rotation_z_matrix(degrees)
    else:
        raise ValueError("axis must be 'x', 'y' or 'z'")

    return matrix @ points


def isometric_projection(points):

    check_points(points)

    angle = np.radians(30)
    c = np.cos(angle)
    s = np.sin(angle)

    projection_matrix = np.array([
        [c, -c, 0, 0],
        [s,  s,  1, 0],
    ], dtype=float)

    return projection_matrix @ points
