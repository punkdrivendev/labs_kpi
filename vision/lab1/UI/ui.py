import tkinter as tk
from tkinter import messagebox

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Polygon

from operations_2d import basic_2d_operations as ops2d
from operations_3d import basic_3d_operations as ops3d

from anim import anim_2d
from anim import anim_3d


X_MIN = -10
X_MAX = 10
Y_MIN = -10
Y_MAX = 10


def run_ui():
    root = tk.Tk()
    root.title("Lab 1 - 2D / 3D transformations")
    root.geometry("1180x760")

    state_2d = {
        "original_points": None,
        "current_points": None,
        "animation": None,
    }

    state_3d = {
        "original_points": None,
        "current_points": None,
        "animation": None,
    }

    controls = tk.Frame(root)
    controls.pack(
        side=tk.LEFT,
        fill=tk.Y,
        padx=15,
        pady=15,
    )

    figure = Figure(figsize=(7, 7))
    ax = figure.add_subplot(111)

    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_aspect("equal")
    ax.axhline(0)
    ax.axvline(0)
    ax.grid(True)

    canvas = FigureCanvasTkAgg(
        figure,
        master=root,
    )

    canvas.get_tk_widget().pack(
        side=tk.RIGHT,
        fill=tk.BOTH,
        expand=True,
        padx=15,
        pady=15,
    )

    triangle_line, = ax.plot(
        [],
        [],
        marker="o",
    )

    trajectory_lines = [
        ax.plot([], [], linestyle="--")[0]
        for _ in range(3)
    ]

    trajectory_x = [[], [], []]
    trajectory_y = [[], [], []]
    edge_lines_3d = [
        ax.plot([], [])[0]
        for _ in anim_3d.EDGES
    ]

    face_patches_3d = []

    for _ in anim_3d.FACES:
        patch = Polygon(
            [[0, 0], [0, 0], [0, 0]],
            closed=True,
            alpha=0.4,
        )

        ax.add_patch(patch)
        face_patches_3d.append(patch)

    mode = tk.StringVar(value="2D")

    tk.Label(
        controls,
        text="Task mode",
        font=("Arial", 14, "bold"),
    ).pack(pady=(0, 5))

    mode_switch = tk.Frame(controls)
    mode_switch.pack(pady=(0, 10))

    panel_container = tk.Frame(controls)
    panel_container.pack(fill=tk.BOTH, expand=True)

    panel_2d = tk.Frame(panel_container)
    panel_3d = tk.Frame(panel_container)

    def set_2d_visible(visible):
        triangle_line.set_visible(visible)

        for line in trajectory_lines:
            line.set_visible(visible)

    def set_3d_visible(visible):
        for line in edge_lines_3d:
            line.set_visible(visible)

        for patch in face_patches_3d:
            patch.set_visible(visible)

    def stop_all_animations():
        if state_2d["animation"] is not None:
            anim_2d.stop_animation(
                state_2d["animation"]
            )
            state_2d["animation"] = None

        if state_3d["animation"] is not None:
            anim_3d.stop_animation(
                state_3d["animation"]
            )
            state_3d["animation"] = None

    def switch_mode():
        stop_all_animations()

        if mode.get() == "2D":
            panel_3d.pack_forget()
            panel_2d.pack(fill=tk.BOTH, expand=True)

            set_2d_visible(True)
            set_3d_visible(False)

        else:
            panel_2d.pack_forget()
            panel_3d.pack(fill=tk.BOTH, expand=True)

            set_2d_visible(False)
            set_3d_visible(True)

            if state_3d["original_points"] is None:
                draw_3d()

        canvas.draw_idle()

    tk.Radiobutton(
        mode_switch,
        text="2D",
        variable=mode,
        value="2D",
        command=switch_mode,
    ).pack(side=tk.LEFT)

    tk.Radiobutton(
        mode_switch,
        text="3D",
        variable=mode,
        value="3D",
        command=switch_mode,
    ).pack(side=tk.LEFT)

    tk.Label(
        panel_2d,
        text="Task I — triangle",
        font=("Arial", 13, "bold"),
    ).grid(
        row=0,
        column=0,
        columnspan=3,
        pady=5,
    )

    tk.Label(panel_2d, text="Point").grid(row=1, column=0)
    tk.Label(panel_2d, text="X").grid(row=1, column=1)
    tk.Label(panel_2d, text="Y").grid(row=1, column=2)

    entries = {}

    default_coords = {
        "A": (1, 3),
        "B": (1, 1),
        "C": (4, 1),
    }

    for row, point_name in enumerate(("A", "B", "C"), start=2):
        tk.Label(panel_2d, text=point_name).grid(
            row=row,
            column=0,
        )

        x_entry = tk.Entry(
            panel_2d,
            width=8,
        )

        y_entry = tk.Entry(
            panel_2d,
            width=8,
        )

        x_entry.grid(row=row, column=1)
        y_entry.grid(row=row, column=2)

        x_entry.insert(
            0,
            str(default_coords[point_name][0]),
        )

        y_entry.insert(
            0,
            str(default_coords[point_name][1]),
        )

        entries[point_name] = (
            x_entry,
            y_entry,
        )

    # Translation sliders

    tk.Label(
        panel_2d,
        text="Translation",
        font=("Arial", 11, "bold"),
    ).grid(
        row=6,
        column=0,
        columnspan=3,
        pady=(15, 2),
    )

    tk.Label(panel_2d, text="dx").grid(row=7, column=0)

    dx_slider = tk.Scale(
        panel_2d,
        from_=-5,
        to=5,
        resolution=0.5,
        orient=tk.HORIZONTAL,
        length=180,
    )

    dx_slider.grid(
        row=7,
        column=1,
        columnspan=2,
    )

    tk.Label(panel_2d, text="dy").grid(row=8, column=0)

    dy_slider = tk.Scale(
        panel_2d,
        from_=-5,
        to=5,
        resolution=0.5,
        orient=tk.HORIZONTAL,
        length=180,
    )

    dy_slider.grid(
        row=8,
        column=1,
        columnspan=2,
    )

    tk.Label(
        panel_2d,
        text="Cyclic rotation + scaling",
        font=("Arial", 11, "bold"),
    ).grid(
        row=9,
        column=0,
        columnspan=3,
        pady=(15, 2),
    )

    tk.Label(
        panel_2d,
        text="Degrees/frame",
    ).grid(row=10, column=0)

    angle_2d_slider = tk.Scale(
        panel_2d,
        from_=1,
        to=15,
        resolution=1,
        orient=tk.HORIZONTAL,
        length=180,
    )

    angle_2d_slider.set(5)

    angle_2d_slider.grid(
        row=10,
        column=1,
        columnspan=2,
    )

    tk.Label(
        panel_2d,
        text="Scale change",
    ).grid(row=11, column=0)

    scale_2d_slider = tk.Scale(
        panel_2d,
        from_=0.0,
        to=0.5,
        resolution=0.05,
        orient=tk.HORIZONTAL,
        length=180,
    )

    scale_2d_slider.set(0.25)

    scale_2d_slider.grid(
        row=11,
        column=1,
        columnspan=2,
    )

    def display_2d(points):
        x = points[0]
        y = points[1]

        triangle_line.set_data(
            np.append(x, x[0]),
            np.append(y, y[0]),
        )

        canvas.draw_idle()

    def draw_2d():
        if state_2d["animation"] is not None:
            anim_2d.stop_animation(
                state_2d["animation"]
            )
            state_2d["animation"] = None

        try:
            coords = {}

            for name in ("A", "B", "C"):
                x_entry, y_entry = entries[name]

                coords[name] = (
                    float(x_entry.get()),
                    float(y_entry.get()),
                )

        except ValueError:
            messagebox.showerror(
                "Error",
                "2D coordinates must be numbers",
            )
            return

        points = np.array([
            [
                coords["A"][0],
                coords["B"][0],
                coords["C"][0],
            ],
            [
                coords["A"][1],
                coords["B"][1],
                coords["C"][1],
            ],
            [1, 1, 1],
        ], dtype=float)

        if not ops2d.inside_window(
            points,
            X_MIN,
            X_MAX,
            Y_MIN,
            Y_MAX,
        ):
            messagebox.showerror(
                "Error",
                "Triangle is outside the graphics window",
            )
            return

        state_2d["original_points"] = points.copy()
        state_2d["current_points"] = points.copy()

        anim_2d.clear_trajectory(
            trajectory_lines,
            trajectory_x,
            trajectory_y,
        )

        display_2d(points)

    def move_2d():
        if state_2d["current_points"] is None:
            messagebox.showerror(
                "Error",
                "Draw the triangle first",
            )
            return

        new_points = ops2d.move_2d(
            state_2d["current_points"],
            dx_slider.get(),
            dy_slider.get(),
        )

        if not ops2d.inside_window(
            new_points,
            X_MIN,
            X_MAX,
            Y_MIN,
            Y_MAX,
        ):
            messagebox.showerror(
                "Error",
                "Translation moves the triangle outside the window",
            )
            return

        state_2d["current_points"] = new_points
        display_2d(new_points)

    def start_2d_animation():
        if state_2d["current_points"] is None:
            messagebox.showerror(
                "Error",
                "Draw the triangle first",
            )
            return

        if state_2d["animation"] is not None:
            anim_2d.stop_animation(
                state_2d["animation"]
            )

        try:
            state_2d["animation"] = (
                anim_2d.start_rotate_scale_animation(
                    figure,
                    canvas,
                    triangle_line,
                    trajectory_lines,
                    trajectory_x,
                    trajectory_y,
                    state_2d,
                    angle_2d_slider.get(),
                    scale_2d_slider.get(),
                    X_MIN,
                    X_MAX,
                    Y_MIN,
                    Y_MAX,
                )
            )

        except ValueError as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def stop_2d_animation():
        if state_2d["animation"] is not None:
            anim_2d.stop_animation(
                state_2d["animation"]
            )
            state_2d["animation"] = None

    def reset_2d():
        stop_2d_animation()

        if state_2d["original_points"] is None:
            return

        state_2d["current_points"] = (
            state_2d["original_points"].copy()
        )

        anim_2d.clear_trajectory(
            trajectory_lines,
            trajectory_x,
            trajectory_y,
        )

        display_2d(
            state_2d["current_points"]
        )

    tk.Button(
        panel_2d,
        text="Draw triangle",
        width=22,
        command=draw_2d,
    ).grid(
        row=13,
        column=0,
        columnspan=3,
        pady=(15, 4),
    )

    tk.Button(
        panel_2d,
        text="Move",
        width=22,
        command=move_2d,
    ).grid(
        row=14,
        column=0,
        columnspan=3,
        pady=4,
    )

    tk.Button(
        panel_2d,
        text="Start rotation + scaling",
        width=22,
        command=start_2d_animation,
    ).grid(
        row=15,
        column=0,
        columnspan=3,
        pady=4,
    )

    tk.Button(
        panel_2d,
        text="Stop",
        width=22,
        command=stop_2d_animation,
    ).grid(
        row=16,
        column=0,
        columnspan=3,
        pady=4,
    )

    tk.Button(
        panel_2d,
        text="Reset",
        width=22,
        command=reset_2d,
    ).grid(
        row=17,
        column=0,
        columnspan=3,
        pady=4,
    )

    tk.Label(
        panel_3d,
        text="Task II — triangular pyramid",
        font=("Arial", 13, "bold"),
    ).pack(pady=5)

    tk.Label(
        panel_3d,
        text="Pyramid size",
    ).pack()

    size_3d_slider = tk.Scale(
        panel_3d,
        from_=0.5,
        to=4.0,
        resolution=0.25,
        orient=tk.HORIZONTAL,
        length=220,
    )

    size_3d_slider.set(2.0)
    size_3d_slider.pack()

    tk.Label(
        panel_3d,
        text="Rotation degrees/frame",
    ).pack()

    angle_3d_slider = tk.Scale(
        panel_3d,
        from_=1,
        to=15,
        resolution=1,
        orient=tk.HORIZONTAL,
        length=220,
    )

    angle_3d_slider.set(5)
    angle_3d_slider.pack()

    tk.Label(
        panel_3d,
        text="Animation speed (ms)",
    ).pack()

    speed_3d_slider = tk.Scale(
        panel_3d,
        from_=20,
        to=200,
        resolution=10,
        orient=tk.HORIZONTAL,
        length=220,
    )

    speed_3d_slider.set(60)
    speed_3d_slider.pack()

    def display_3d(points):
        projected = ops3d.isometric_projection(points)

        anim_3d.update_pyramid_artists(
            projected,
            edge_lines_3d,
            face_patches_3d,
        )

        for line in edge_lines_3d:
            line.set_alpha(1.0)

        for patch in face_patches_3d:
            patch.set_alpha(0.35)

        canvas.draw_idle()

    def draw_3d():
        if state_3d["animation"] is not None:
            anim_3d.stop_animation(
                state_3d["animation"]
            )
            state_3d["animation"] = None

        points = ops3d.make_triangular_pyramid(
            size_3d_slider.get()
        )

        state_3d["original_points"] = points.copy()
        state_3d["current_points"] = points.copy()

        display_3d(points)

    def start_3d_animation():
        if state_3d["original_points"] is None:
            draw_3d()

        if state_3d["animation"] is not None:
            anim_3d.stop_animation(
                state_3d["animation"]
            )

        try:
            state_3d["animation"] = (
                anim_3d.start_pyramid_animation(
                    figure,
                    canvas,
                    edge_lines_3d,
                    face_patches_3d,
                    state_3d,
                    angle_3d_slider.get(),
                    speed_3d_slider.get(),
                )
            )

        except ValueError as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def stop_3d_animation():
        if state_3d["animation"] is not None:
            anim_3d.stop_animation(
                state_3d["animation"]
            )
            state_3d["animation"] = None

    def reset_3d():
        stop_3d_animation()
        draw_3d()

    tk.Button(
        panel_3d,
        text="Draw pyramid",
        width=22,
        command=draw_3d,
    ).pack(pady=(15, 4))

    tk.Button(
        panel_3d,
        text="Start cyclic rotation",
        width=22,
        command=start_3d_animation,
    ).pack(pady=4)

    tk.Button(
        panel_3d,
        text="Stop",
        width=22,
        command=stop_3d_animation,
    ).pack(pady=4)

    tk.Button(
        panel_3d,
        text="Reset",
        width=22,
        command=reset_3d,
    ).pack(pady=4)

    set_2d_visible(True)
    set_3d_visible(False)

    panel_2d.pack(
        fill=tk.BOTH,
        expand=True,
    )

    root.mainloop()
