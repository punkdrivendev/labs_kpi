import tkinter as tk

from UI.ui import ImageUI


def main():
    root = tk.Tk()

    app = ImageUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()
