from operations_2d import basic_2d_operations


def scaling_animation(points, frame):
    scale = 1 + frame * 0.01

    new_points = basic_2d_operations.scale_figure(
        points,
        scale
    )

    return new_points


def rotation_animation(points, frame):
    angle = frame * 5

    new_points = basic_2d_operations.rotate_2d(
        points,
        angle
    )

    return new_points


def update(frame):
    new_points = scaling_animation(
        original_points,
        frame
    )

    new_points = rotation_animation(
        new_points,
        frame
    )

    x = new_points[0]
    y = new_points[1]

    line.set_data(
        x + [x[0]],
        y + [y[0]]
    )

    return line,

def increase(points, frame):
    return scaling_animation(points, frame, 1)

def decrease(points, frame):
    return scaling_animation(points, frame, -1)

def rotate_left(points, frame):
    return rotation_animation(points, frame, 1)

def rotate_right(points, frame):
    return rotation_animation(points, frame, -1)

def scale_and_rotate(points, frame, rotation_way, scale_way):

    if scale_way == 1:
        new_points = increase(points, frame)
    else:
        new_points = decrease(points, frame)

    if rotation_way == 1:
        new_points = rotate_left(new_points, frame)
    else:
        new_point = rotate_right(new_points, frame)

    return new_points
