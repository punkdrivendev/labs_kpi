import tkinter as tk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def UI():
    root = tk.Tk()
    root.title("2D Transformations")
    root.geometry("1000x650")

    # =========================================================
    # LEFT PANEL
    # =========================================================

    controls = tk.Frame(root)
    controls.pack(
        side=tk.LEFT,
        padx=15,
        pady=15,
        fill=tk.Y
    )

    # =========================================================
    # TRIANGLE COORDINATES
    # =========================================================

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

    tk.Label(controls, text="Point").grid(row=1, column=0)
    tk.Label(controls, text="X").grid(row=1, column=1)
    tk.Label(controls, text="Y").grid(row=1, column=2)

    # A
    tk.Label(controls, text="A").grid(row=2, column=0)

    x1_entry = tk.Entry(controls, width=8)
    y1_entry = tk.Entry(controls, width=8)

    x1_entry.grid(row=2, column=1)
    y1_entry.grid(row=2, column=2)

    # B
    tk.Label(controls, text="B").grid(row=3, column=0)

    x2_entry = tk.Entry(controls, width=8)
    y2_entry = tk.Entry(controls, width=8)

    x2_entry.grid(row=3, column=1)
    y2_entry.grid(row=3, column=2)

    # C
    tk.Label(controls, text="C").grid(row=4, column=0)

    x3_entry = tk.Entry(controls, width=8)
    y3_entry = tk.Entry(controls, width=8)

    x3_entry.grid(row=4, column=1)
    y3_entry.grid(row=4, column=2)

    # =========================================================
    # ROTATION
    # =========================================================

    tk.Label(
        controls,
        text="Rotation",
        font=("Arial", 12, "bold")
    ).grid(
        row=6,
        column=0,
        columnspan=3,
        pady=(20, 5)
    )

    tk.Label(
        controls,
        text="Degrees:"
    ).grid(row=7, column=0)

    degrees_entry = tk.Entry(
        controls,
        width=10
    )

    degrees_entry.grid(
        row=7,
        column=1,
        columnspan=2
    )

    # =========================================================
    # SCALE
    # =========================================================

    tk.Label(
        controls,
        text="Scaling",
        font=("Arial", 12, "bold")
    ).grid(
        row=8,
        column=0,
        columnspan=3,
        pady=(20, 5)
    )

    tk.Label(
        controls,
        text="Scale:"
    ).grid(row=9, column=0)

    scale_entry = tk.Entry(
        controls,
        width=10
    )

    scale_entry.grid(
        row=9,
        column=1,
        columnspan=2
    )

    # =========================================================
    # MATPLOTLIB
    # =========================================================

    figure = Figure(figsize=(6, 6))
    ax = figure.add_subplot(111)

    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_aspect("equal")
    ax.grid(True)

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

    # =========================================================
    # CALLBACK FUNCTIONS
    # =========================================================

    def on_draw():
        """
        Кнопка Draw.

        Тут зчитуєш:
        x1, y1
        x2, y2
        x3, y3

        І створюєш points.
        """

        # Наприклад:
        #
        # x1 = float(x1_entry.get())
        # y1 = float(y1_entry.get())
        #
        # ...
        #
        # points = [
        #     [x1, x2, x3],
        #     [y1, y2, y3],
        #     [1,  1,  1]
        # ]
        #
        # ТУТ ТВОЯ ФУНКЦІЯ:
        #
        # draw_figure(points, ...)
        #
        # canvas.draw_idle()

        print("DRAW")


    def on_rotate_left():
        """
        Кнопка Rotate left.
        """

        degrees = float(degrees_entry.get())

        # ТУТ ТВОЯ ФУНКЦІЯ:
        #
        # current_points = rotate_left(
        #     current_points,
        #     degrees
        # )

        print("ROTATE LEFT:", degrees)


    def on_rotate_right():
        """
        Кнопка Rotate right.
        """

        degrees = float(degrees_entry.get())

        # ТУТ ТВОЯ ФУНКЦІЯ:
        #
        # current_points = rotate_right(
        #     current_points,
        #     degrees
        # )

        print("ROTATE RIGHT:", degrees)


    def on_increase():
        """
        Кнопка Increase.
        """

        scale = float(scale_entry.get())

        # ТУТ ТВОЯ ФУНКЦІЯ:
        #
        # current_points = increase(
        #     current_points,
        #     scale
        # )

        print("INCREASE:", scale)


    def on_decrease():
        """
        Кнопка Decrease.
        """

        scale = float(scale_entry.get())

        # ТУТ ТВОЯ ФУНКЦІЯ:
        #
        # current_points = decrease(
        #     current_points,
        #     scale
        # )

        print("DECREASE:", scale)


    # =========================================================
    # BUTTONS
    # =========================================================

    tk.Button(
        controls,
        text="Draw",
        width=22,
        command=on_draw
    ).grid(
        row=11,
        column=0,
        columnspan=3,
        pady=(25, 10)
    )

    # ---- ROTATION BUTTONS ----

    tk.Button(
        controls,
        text="← Rotate left",
        width=15,
        command=on_rotate_left
    ).grid(
        row=12,
        column=0,
        columnspan=2,
        pady=5
    )

    tk.Button(
        controls,
        text="Rotate right →",
        width=15,
        command=on_rotate_right
    ).grid(
        row=13,
        column=0,
        columnspan=2,
        pady=5
    )

    # ---- SCALE BUTTONS ----

    tk.Button(
        controls,
        text="+ Increase",
        width=15,
        command=on_increase
    ).grid(
        row=14,
        column=0,
        columnspan=2,
        pady=(15, 5)
    )

    tk.Button(
        controls,
        text="- Decrease",
        width=15,
        command=on_decrease
    ).grid(
        row=15,
        column=0,
        columnspan=2,
        pady=5
    )

    root.mainloop()


UI()
