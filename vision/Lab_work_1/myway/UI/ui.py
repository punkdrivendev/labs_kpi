import tkinter as tk
from operations_2d import basic_2d_operations

def button_rotate():
    new_x, new_y = rotate_2d(x,y,degrees)


def UI():
    root = tk.Tk()
    root.title("Головне вікно")
    root.geometry("320x240")

    label_def_figure = tk.Label(root, text="Enter coordinates of figure") #defining the figure
    x_entry = tk.Entry(root)
    y_entry = tk.Entry(root)
    label_def_figure.grid(row = 0, column = 1)
    x_entry.grid(row = 1, column = 1)
    y_entry.grid(row = 1, column = 2)





    root.mainloop()
