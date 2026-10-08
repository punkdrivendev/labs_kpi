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
    figure = ax.plot(x,y)
    if fill_bool:
        ax.fill(x,y)
    if peak_bool:
        ax.scatter(x,y)
    ax.grid()

    plt.show(block = False)


def rotate_2d(summits_cords, degrees):
    #which_way is a boolean if true it spins the object right, if not left
    try:
        isinstance(degrees,int)
    except ValueError:
        print("The value is not a whole number, exiting")
    for x in range(sizeof(summits_cords)):
        for y in range(sizeof(summits_cords)):
             summits_cords_rotated[x,:] = (summits_cords[x,:]*np.cos(degrees) - summits_cords[:,y]*np.sin(degrees))
             summits_cords_rotated[:,y] = (summits_cords[x,:]*np.sin(degrees) - summits_cords[:,y]*np.cos(degrees))

    


    print("bombo")



x = [1,4,1]
y = [1,1,3]
draw_figure(x,y,True,True)
