import numpy as np
from matplotlib.animation import FuncAnimation

from operations_3d import basic_3d_operations as ops


EDGES = [
    (0, 1),
    (1, 2),
    (2, 0),
    (0, 3),
    (1, 3),
    (2, 3),
]

FACES = [
    (0, 1, 2),
    (0, 1, 3),
    (1, 2, 3),
    (2, 0, 3),
]


def stop_animation(animation):
    if animation is not None:
        animation.event_source.stop()


def update_pyramid_artists(projected, edge_lines, face_patches):
    for line, (a, b) in zip(edge_lines, EDGES):
        line.set_data(
            [projected[0, a], projected[0, b]],
            [projected[1, a], projected[1, b]],
        )

    for patch, face in zip(face_patches, FACES):
        polygon = np.array([
            [projected[0, vertex], projected[1, vertex]]
            for vertex in face
        ])

        patch.set_xy(polygon)


def start_pyramid_animation(
    figure,
    canvas,
    edge_lines,
    face_patches,
    state,
    angle_step,
    interval_ms,
):
    if angle_step == 0:
        raise ValueError("Angle step cannot be zero")

    base_points = state["original_points"].copy()

    frames = int(np.ceil(360 / abs(angle_step)))
    frames = max(1, min(frames, 1000))

    contour_colors = [
        "black",
        "darkred",
        "darkgreen",
        "navy",
        "purple",
    ]

    fill_colors = [
        "lightblue",
        "lightgreen",
        "khaki",
        "plum",
        "salmon",
    ]

    def update(frame):
        angle = frame * angle_step

        rotated = ops.rotate_3d(
            base_points,
            angle,
            axis="z",
        )

        state["current_points"] = rotated

        projected = ops.isometric_projection(rotated)

        update_pyramid_artists(
            projected,
            edge_lines,
            face_patches,
        )

        fade = 0.15 + 0.85 * (
            0.5 + 0.5 * np.sin(2 * np.pi * frame / frames)
        )

        color_index = int(
            frame * len(contour_colors) / frames
        ) % len(contour_colors)

        for line in edge_lines:
            line.set_alpha(fade)
            line.set_color(contour_colors[color_index])

        for patch in face_patches:
            patch.set_alpha(0.15 + 0.45 * fade)
            patch.set_edgecolor(contour_colors[color_index])
            patch.set_facecolor(fill_colors[color_index])

        return (*edge_lines, *face_patches)

    animation = FuncAnimation(
        figure,
        update,
        frames=frames,
        interval=int(interval_ms),
        repeat=True,
        blit=False,
    )

    canvas.draw_idle()
    return animation
