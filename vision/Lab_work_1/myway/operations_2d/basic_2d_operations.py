import numpy as np
import matplotlib.pyplot as plt


def check_points(points):
    if not isinstance(points, np.ndarray):
        raise TypeError("Points must be a numpy array")

    if points.shape != (3, 3):
        raise ValueError("Points must be a 3 by 3 matrix")


def draw_figure(points, fill_bool, peak_bool):
    # points =
    # [
    #   [x1, x2, x3],
    #   [y1, y2, y3],
    #   [1,  1,  1]
    # ]

    check_points(points)

    if not isinstance(fill_bool, bool) or not isinstance(peak_bool, bool):
        raise TypeError(
            "fill_bool and peak_bool parameters must be boolean values"
        )

    x_cords = points[0]
    y_cords = points[1]

    x_plot = np.append(x_cords, x_cords[0])
    y_plot = np.append(y_cords, y_cords[0])

    fig, ax = plt.subplots()

    line, = ax.plot(x_plot, y_plot)

    if fill_bool:
        ax.fill(x_cords, y_cords)

    if peak_bool:
        ax.scatter(x_cords, y_cords)

    ax.grid()
    ax.set_aspect("equal")

    plt.show(block=False)

    return fig, ax, line


def rotate_2d(points, degrees):
    check_points(points)

    if not isinstance(degrees, (int, float)):
        raise TypeError("degrees must be a number")

    angle = np.radians(degrees)

    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle),  np.cos(angle), 0],
        [0,              0,             1]
    ])

    points_rotated = rotation_matrix @ points

    return points_rotated


def scale_figure(points, scale):
    check_points(points)

    if not isinstance(scale, (int, float)):
        raise TypeError("Scale must be a number")

    scale_matrix = np.array([
        [scale, 0,     0],
        [0,     scale, 0],
        [0,     0,     1]
    ])

    points_scaled = scale_matrix @ points

    return points_scaled
