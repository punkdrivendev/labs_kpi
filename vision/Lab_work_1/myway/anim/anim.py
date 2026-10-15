import numpy as np

from matplotlib.animation import FuncAnimation
from tkinter import messagebox

from operations_2d import basic_2d_operations as ops


def stop_animation(animation):
    if animation is not None:
        animation.event_source.stop()


def clear_trajectory(
    trajectory_lines,
    trajectory_x,
    trajectory_y
):
    for i in range(3):
        trajectory_x[i].clear()
        trajectory_y[i].clear()

        trajectory_lines[i].set_data([], [])


def start_rotate_scale_animation(
    figure,
    canvas,
    line,
    trajectory_lines,
    trajectory_x,
    trajectory_y,
    state,
    angle_step,
    scale_change,
    x_min,
    x_max,
    y_min,
    y_max
):

    base_points = state["current_points"].copy()

    if angle_step == 0:
        raise ValueError("Angle step cannot be zero")

    if scale_change < 0 or scale_change >= 1:
        raise ValueError(
            "Scale change must be >= 0 and < 1"
        )

    frames = int(
        np.ceil(
            360 / abs(angle_step)
        )
    )

    frames = max(
        1,
        min(frames, 1000)
    )

    # -------------------------------------------------
    # перевіряємо наперед, чи фігура не вилетить за межі
    # -------------------------------------------------

    for frame in range(frames):

        angle = frame * angle_step

        scale = (
            1
            + scale_change
            * np.sin(
                2 * np.pi * frame / frames
            )
        )

        test_points = ops.rotate_scale_2d(
            base_points,
            angle,
            scale
        )

        if not ops.inside_window(
            test_points,
            x_min,
            x_max,
            y_min,
            y_max
        ):
            raise ValueError(
                "Animation moves triangle outside the window"
            )

    def update(frame):

        if frame == 0:
            clear_trajectory(
                trajectory_lines,
                trajectory_x,
                trajectory_y
            )

        angle = frame * angle_step

        scale = (
            1
            + scale_change
            * np.sin(
                2 * np.pi * frame / frames
            )
        )

        new_points = ops.rotate_scale_2d(
            base_points,
            angle,
            scale
        )

        state["current_points"] = new_points

        x = new_points[0]
        y = new_points[1]

        x_plot = np.append(
            x,
            x[0]
        )

        y_plot = np.append(
            y,
            y[0]
        )

        line.set_data(
            x_plot,
            y_plot
        )

        for i in range(3):

            trajectory_x[i].append(
                x[i]
            )

            trajectory_y[i].append(
                y[i]
            )

            trajectory_lines[i].set_data(
                trajectory_x[i],
                trajectory_y[i]
            )

        return (
            line,
            *trajectory_lines
        )

    animation = FuncAnimation(
        figure,
        update,
        frames=frames,
        interval=50,
        repeat=True,
        blit=False
    )

    canvas.draw_idle()

    return animation
