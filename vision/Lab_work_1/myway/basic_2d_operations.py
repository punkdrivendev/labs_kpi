import numpy as np
import math as mt
import matplotlib.pyplot as plt
import sys

def draw_figure(x,y, fill_bool, peak_bool):
    if not isinstance(x,list) or not isinstance(y,list):
        raise TypeError("X and Y must be a list of coordinates")
    if not type(fill_bool) == bool or not type(peak_bool) == bool:
        raise TypeError("fill_bool and peak_bool parametrs must be a boolean value")

    fig, ax = plt.subplots();
    ax.plot(x,y)
    if fill_bool:
        ax.fill(x,y)
    if peak_bool:
        ax.scatter(x,y)
    ax.grid()

    plt.show()


def rotate_2d(x_cords, y_cords, degrees):
    if not isinstance(degrees, int):
        raise TypeError("degrees must be an integer")

    angle = np.radians(degrees)

    x_rotated = []
    y_rotated = []

    for i in range(len(x_cords)):
        x = x_cords[i]
        y = y_cords[i]

        new_x = x * np.cos(angle) - y * np.sin(angle)
        new_y = x * np.sin(angle) + y * np.cos(angle)

        x_rotated.append(new_x)
        y_rotated.append(new_y)

    draw_figure(x_rotated, y_rotated, False, False)



x = [1,4,1]
y = [1,1,3]
draw_figure(x,y,True,True)
