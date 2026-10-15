# UI/ui.py

import tkinter as tk
from tkinter import messagebox

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from operations_2d import basic_2d_operations as ops
from anim import anim


X_MIN = -10
X_MAX = 10

Y_MIN = -10
Y_MAX = 10


def run_ui():
    root = tk.Tk()

    root.title("Lab 1 - 2D transformations")
    root.geometry("1100x700")

    state = {
        "original_points": None,
        "current_points": None,
        "animation": None
    }

    controls = tk.Frame(root)

    controls.pack(
        side=tk.LEFT,
        fill=tk.Y,
        padx=15,
        pady=15
    )

    tk.Label(
        controls,
        text="Triangle coordinates",
        font=("Arial", 14, "bold")
    ).grid(
        row=0,
        column=0,
        columnspan=3,
        pady=10
    )

    tk.Label(
        controls,
        text="Point"
    ).grid(
        row=1,
        column=0
    )

    tk.Label(
        controls,
        text="X"
    ).grid(
        row=1,
        column=1
    )

    tk.Label(
        controls,
        text="Y"
    ).grid(
        row=1,
        column=2
    )

    tk.Label(
        controls,
        text="A"
    ).grid(
        row=2,
        column=0
    )

    x1_entry = tk.Entry(
        controls,
        width=8
    )

    y1_entry = tk.Entry(
        controls,
        width=8
    )

    x1_entry.grid(
        row=2,
        column=1
    )

    y1_entry.grid(
        row=2,
        column=2
    )

    tk.Label(
        controls,
        text="B"
    ).grid(
        row=3,
        column=0
    )

    x2_entry = tk.Entry(
        controls,
        width=8
    )

    y2_entry = tk.Entry(
        controls,
        width=8
    )

    x2_entry.grid(
        row=3,
        column=1
    )

    y2_entry.grid(
        row=3,
        column=2
    )

    tk.Label(
        controls,
        text="C"
    ).grid(
        row=4,
        column=0
    )

    x3_entry = tk.Entry(
        controls,
        width=8
    )

    y3_entry = tk.Entry(
        controls,
        width=8
    )

    x3_entry.grid(
        row=4,
        column=1
    )

    y3_entry.grid(
        row=4,
        column=2
    )

    x1_entry.insert(0, "1")
    y1_entry.insert(0, "3")

    x2_entry.insert(0, "1")
    y2_entry.insert(0, "1")

    x3_entry.insert(0, "4")
    y3_entry.insert(0, "1")

    tk.Label(
        controls,
        text="Translation",
        font=("Arial", 12, "bold")
    ).grid(
        row=6,
        column=0,
        columnspan=3,
        pady=(20, 5)
    )

    tk.Label(
        controls,
        text="dx"
    ).grid(
        row=7,
        column=0
    )

    dx_entry = tk.Entry(
        controls,
        width=8
    )

    dx_entry.grid(
        row=7,
        column=1
    )

    tk.Label(
        controls,
        text="dy"
    ).grid(
        row=8,
        column=0
    )

    dy_entry = tk.Entry(
        controls,
        width=8
    )

    dy_entry.grid(
        row=8,
        column=1
    )

    dx_entry.insert(0, "1")
    dy_entry.insert(0, "1")

    tk.Label(
        controls,
        text="Rotation + scaling",
        font=("Arial", 12, "bold")
    ).grid(
        row=10,
        column=0,
        columnspan=3,
        pady=(20, 5)
    )

    tk.Label(
        controls,
        text="Degrees/frame"
    ).grid(
        row=11,
        column=0
    )

    degrees_entry = tk.Entry(
        controls,
        width=8
    )

    degrees_entry.grid(
        row=11,
        column=1
    )

    degrees_entry.insert(
        0,
        "5"
    )

    tk.Label(
        controls,
        text="Scale change"
    ).grid(
        row=12,
        column=0
    )

    scale_entry = tk.Entry(
        controls,
        width=8
    )

    scale_entry.grid(
        row=12,
        column=1
    )

    scale_entry.insert(
        0,
        "0.25"
    )

    figure = Figure(
        figsize=(7, 7)
    )

    ax = figure.add_subplot(111)

    ax.set_xlim(
        X_MIN,
        X_MAX
    )

    ax.set_ylim(
        Y_MIN,
        Y_MAX
    )

    ax.set_aspect(
        "equal"
    )

    ax.axhline(0)
    ax.axvline(0)

    ax.grid(True)

    line, = ax.plot(
        [],
        [],
        marker="o"
    )

    trajectory_lines = [
        ax.plot(
            [],
            [],
            linestyle="--"
        )[0]
        for _ in range(3)
    ]

    trajectory_x = [
        [],
        [],
        []
    ]

    trajectory_y = [
        [],
        [],
        []
    ]

    canvas = FigureCanvasTkAgg(
        figure,
        master=root
    )

    canvas.get_tk_widget().pack(
        side=tk.RIGHT,
        fill=tk.BOTH,
        expand=True,
        padx=15,
        pady=15
    )

    def display_points(points):
        x = points[0]
        y = points[1]

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

        canvas.draw_idle()

    def on_draw():
        if state["animation"] is not None:
            anim.stop_animation(
                state["animation"]
            )

            state["animation"] = None

        try:
            x1 = float(
                x1_entry.get()
            )

            y1 = float(
                y1_entry.get()
            )

            x2 = float(
                x2_entry.get()
            )

            y2 = float(
                y2_entry.get()
            )

            x3 = float(
                x3_entry.get()
            )

            y3 = float(
                y3_entry.get()
            )

        except ValueError:
            messagebox.showerror(
                "Error",
                "Coordinates must be numbers"
            )

            return

        points = np.array([
            [x1, x2, x3],
            [y1, y2, y3],
            [1, 1, 1]
        ], dtype=float)

        if not ops.inside_window(
            points,
            X_MIN,
            X_MAX,
            Y_MIN,
            Y_MAX
        ):
            messagebox.showerror(
                "Error",
                "Triangle is outside the window"
            )

            return

        state["original_points"] = (
            points.copy()
        )

        state["current_points"] = (
            points.copy()
        )

        anim.clear_trajectory(
            trajectory_lines,
            trajectory_x,
            trajectory_y
        )

        display_points(
            points
        )

    def on_move():
        if state["current_points"] is None:
            messagebox.showerror(
                "Error",
                "Draw triangle first"
            )

            return

        try:
            dx = float(
                dx_entry.get()
            )

            dy = float(
                dy_entry.get()
            )

        except ValueError:
            messagebox.showerror(
                "Error",
                "dx and dy must be numbers"
            )

            return

        new_points = ops.move_2d(
            state["current_points"],
            dx,
            dy
        )

        if not ops.inside_window(
            new_points,
            X_MIN,
            X_MAX,
            Y_MIN,
            Y_MAX
        ):
            messagebox.showerror(
                "Error",
                "Triangle leaves the window"
            )

            return

        state["current_points"] = (
            new_points
        )

        display_points(
            new_points
        )

    def on_start_animation():
        if state["current_points"] is None:
            messagebox.showerror(
                "Error",
                "Draw triangle first"
            )

            return

        try:
            angle_step = float(
                degrees_entry.get()
            )

            scale_change = float(
                scale_entry.get()
            )

        except ValueError:
            messagebox.showerror(
                "Error",
                "Animation parameters must be numbers"
            )

            return

        if state["animation"] is not None:
            anim.stop_animation(
                state["animation"]
            )

            state["animation"] = None

        try:
            state["animation"] = (
                anim.start_rotate_scale_animation(
                    figure,
                    canvas,
                    line,
                    trajectory_lines,
                    trajectory_x,
                    trajectory_y,
                    state,
                    angle_step,
                    scale_change,
                    X_MIN,
                    X_MAX,
                    Y_MIN,
                    Y_MAX
                )
            )

        except ValueError as error:
            messagebox.showerror(
                "Error",
                str(error)
            )

    def on_stop():
        if state["animation"] is not None:
            anim.stop_animation(
                state["animation"]
            )

            state["animation"] = None

    def on_reset():
        on_stop()

        if state["original_points"] is None:
            return

        state["current_points"] = (
            state["original_points"].copy()
        )

        anim.clear_trajectory(
            trajectory_lines,
            trajectory_x,
            trajectory_y
        )

        display_points(
            state["current_points"]
        )

    tk.Button(
        controls,
        text="Draw triangle",
        width=22,
        command=on_draw
    ).grid(
        row=14,
        column=0,
        columnspan=3,
        pady=(25, 5)
    )

    tk.Button(
        controls,
        text="Move",
        width=22,
        command=on_move
    ).grid(
        row=15,
        column=0,
        columnspan=3,
        pady=5
    )

    tk.Button(
        controls,
        text="Start rotation + scaling",
        width=22,
        command=on_start_animation
    ).grid(
        row=16,
        column=0,
        columnspan=3,
        pady=(15, 5)
    )

    tk.Button(
        controls,
        text="Stop",
        width=22,
        command=on_stop
    ).grid(
        row=17,
        column=0,
        columnspan=3,
        pady=5
    )

    tk.Button(
        controls,
        text="Reset",
        width=22,
        command=on_reset
    ).grid(
        row=18,
        column=0,
        columnspan=3,
        pady=5
    )

    root.mainloop()
