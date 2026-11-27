"""Tkinter interface for comparison of remote sensing images."""

from itertools import product
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from UI.tracking import TrackingWindow
from image_loader.loader import load_image
from image_processing.comparison_config import load_comparison_config
from image_processing.processing import (
    GRAYSCALE,
    HSV_VALUE,
    MATCHING_CHANNELS,
    prepare_comparison_channel,
)
from edge_detector.detector import compare_objects


IMAGE_TYPES = [
    ("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff"),
    ("All files", "*.*"),
]
DEFAULT_BLUR_STEP = 2


class ImageUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab 4 · Image Comparison")
        self.root.minsize(520, 1)

        self.original_image = None
        self.second_image = None
        self._roi_window = None
        self.comparison_window = None
        self.tracking_window = None
        self.matching_channel = tk.StringVar(root, value=HSV_VALUE)
        self.clahe = tk.BooleanVar(root, value=True)

        menu = tk.Menu(root)
        tasks = tk.Menu(menu, tearoff=False)
        tasks.add_command(label="Image Comparison", command=root.lift)
        tasks.add_command(label="Object Tracking", command=self.open_tracking)
        menu.add_cascade(label="Lab 4", menu=tasks)
        root.configure(menu=menu)

        body = ttk.Frame(root, padding=10)
        body.pack(fill="both", expand=True)
        inputs = ttk.Frame(body)
        inputs.pack(fill="x")
        ttk.Button(inputs, text="Select image 1",
                   command=self.select_image).grid(row=0, column=0, padx=(0, 6), pady=2, sticky="ew")
        ttk.Button(inputs, text="Select image 2",
                   command=self.select_second_image).grid(row=1, column=0, padx=(0, 6), pady=2, sticky="ew")
        self.file_label = ttk.Label(inputs, text="No image selected", wraplength=350)
        self.file_label.grid(row=0, column=1, sticky="w")
        self.second_file_label = ttk.Label(inputs, text="No image selected", wraplength=350)
        self.second_file_label.grid(row=1, column=1, sticky="w")

        self.preprocessing = ttk.LabelFrame(body, text="Preprocessing")
        self.preprocessing.pack(fill="x", pady=6)
        self.preprocessing.columnconfigure(1, weight=1)
        ttk.Label(self.preprocessing, text="Brightness").grid(row=0, column=0, sticky="w", padx=6)
        self.brightness_slider = tk.Scale(
            self.preprocessing, from_=-255, to=255, orient=tk.HORIZONTAL,
            length=280, showvalue=False, command=self.update_values_label
        )
        self.brightness_slider.set(0)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(self.preprocessing, text="Contrast").grid(row=1, column=0, sticky="w", padx=6)
        self.contrast_slider = tk.Scale(
            self.preprocessing, from_=0.1, to=3.0, resolution=0.1,
            orient=tk.HORIZONTAL, length=280, showvalue=False, command=self.update_values_label
        )
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, sticky="ew", padx=6)

        ttk.Label(self.preprocessing, text="Gaussian blur").grid(row=2, column=0, sticky="w", padx=6)
        self.blur_slider = tk.Scale(
            self.preprocessing, from_=0, to=10, orient=tk.HORIZONTAL, showvalue=False,
            length=280, command=self.update_values_label
        )
        self.blur_slider.set(DEFAULT_BLUR_STEP)
        self.blur_slider.grid(row=2, column=1, sticky="ew", padx=6)

        self.values_label = ttk.Label(self.preprocessing)
        self.values_label.grid(row=3, column=0, columnspan=2, padx=6, pady=4, sticky="w")
        ttk.Button(self.preprocessing, text="Reset", command=self.reset_parameters).grid(
            row=3, column=2, padx=6, pady=4
        )
        self.update_values_label()

        actions = ttk.Frame(body)
        actions.pack(fill="x")
        self.compare_button = ttk.Button(
            actions, text="Compare regions",
            command=self.start_comparison, state="disabled"
        )
        self.compare_button.grid(row=0, column=0, sticky="w", pady=(4, 0))
        self.full_compare_button = ttk.Button(
            actions, text="Compare full images",
            command=self.compare_full_images, state="disabled",
        )
        self.full_compare_button.grid(row=0, column=1, sticky="w", padx=6, pady=(4, 0))
        ttk.Button(actions, text="Load config", command=lambda: self._load_comparison_config(root)).grid(
            row=0, column=2, sticky="w", pady=(4, 0)
        )
        ttk.Label(
            actions,
            text="Select the same object in both images.",
            wraplength=470
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))

        ttk.Separator(body).pack(fill="x", pady=10)
        ttk.Button(body, text="Object Tracking", command=self.open_tracking).pack(anchor="w")

    def open_tracking(self):
        if self.tracking_window is None or not self.tracking_window.winfo_exists():
            self.tracking_window = TrackingWindow(self.root)
        self.tracking_window.lift()

    def _choose_image(self, title):
        path = filedialog.askopenfilename(
            parent=self.root, title=title, filetypes=IMAGE_TYPES,
            initialdir=Path(__file__).resolve().parents[1] / "images",
        )
        if not path:
            return None
        try:
            return load_image(path), Path(path).name
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            messagebox.showerror("Image error", str(exc), parent=self.root)
            return None

    def select_image(self):
        selection = self._choose_image("Select image 1")
        if selection is None:
            return
        rgb, name = selection
        self.original_image = rgb
        self.file_label.config(text=name)
        self._enable_comparison()

    def select_second_image(self):
        selection = self._choose_image("Select image 2")
        if selection is not None:
            self.second_image, name = selection
            self.second_file_label.config(text=name)
            self._enable_comparison()

    def _enable_comparison(self):
        if self.original_image is not None and self.second_image is not None:
            self.compare_button.configure(state="normal")
            self.full_compare_button.configure(state="normal")

    def reset_parameters(self):
        self._set_processing_parameters(0, 1.0, 2 * DEFAULT_BLUR_STEP + 1)

    def _set_processing_parameters(self, brightness, contrast, kernel):
        self.brightness_slider.set(brightness)
        self.contrast_slider.set(contrast)
        self.blur_slider.set((kernel - 1) // 2)
        self.update_values_label()

    def _load_comparison_config(self, window):
        path = filedialog.askopenfilename(
            parent=window,
            title="Load comparison config",
            initialdir=Path(__file__).resolve().parents[1] / "presets",
            filetypes=[("JSON config", "*.json")],
        )
        if not path:
            return False
        try:
            config = load_comparison_config(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Invalid comparison config", str(exc), parent=window)
            return False

        self._set_processing_parameters(
            config["brightness"], config["contrast"], config["gaussian_kernel"]
        )
        self.matching_channel.set(config["channel"])
        self.clahe.set(config["clahe"])
        if self.comparison_window is not None and self.comparison_window.winfo_exists():
            self.comparison_window.event_generate("<<ComparisonConfigLoaded>>")
        return True

    def processing_parameters(self):
        # Each slider step selects the next odd Gaussian kernel.
        kernel_size = 2 * self.blur_slider.get() + 1
        return (
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            kernel_size,
        )

    def update_values_label(self, _=None):
        brightness, contrast, kernel_size = self.processing_parameters()
        self.values_label.config(
            text=f"Brightness: {brightness}    "
                 f"Contrast: {contrast:.1f}    "
                 f"Gaussian kernel: {kernel_size} × {kernel_size}"
        )

    @staticmethod
    def _photo(image, max_size=(1200, 800)):
        pil = Image.fromarray(np.clip(image, 0, 255).astype(np.uint8))
        pil.thumbnail(max_size)
        return ImageTk.PhotoImage(pil)

    def compare_full_images(self):
        if self.original_image is None or self.second_image is None:
            return
        first_mask = np.full(self.original_image.shape[:2], 255, dtype=np.uint8)
        second_mask = np.full(self.second_image.shape[:2], 255, dtype=np.uint8)
        self.show_comparison(
            self.original_image, self.second_image, first_mask, second_mask, full_images=True
        )

    def start_comparison(self):
        if self.original_image is None or self.second_image is None:
            return
        if self._roi_window is not None and self._roi_window.winfo_exists():
            self._roi_window.lift()
            return
        second_image = self.second_image

        def select_second_region(first, first_mask):
            self._select_region(
                second_image, "Image 2",
                lambda second: self._outline_object(
                    second, lambda second_mask: self.show_comparison(
                        first, second, first_mask, second_mask
                    )
                ),
            )

        self._select_region(
            self.original_image, "Image 1",
            lambda first: self._outline_object(
                first, lambda mask: select_second_region(first, mask)
            ),
        )

    def _select_region(self, image, title, callback):
        window = tk.Toplevel(self.root)
        self._roi_window = window
        window.title(title)
        window.transient(self.root)

        pil = Image.fromarray(image)
        pil.thumbnail((1100, 750))
        display_w, display_h = pil.size
        photo = ImageTk.PhotoImage(pil)
        tk.Label(window, text="Drag a rectangle around the object and some surrounding context.").pack(pady=5)
        canvas = tk.Canvas(window, width=display_w, height=display_h,
                           highlightthickness=0, cursor="crosshair")
        canvas.pack()
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo

        state = {"start": None, "bounds": None, "rect": None}

        def coords(event):
            return (max(0, min(display_w, event.x)),
                    max(0, min(display_h, event.y)))

        def press(event):
            state["start"] = coords(event)
            state["bounds"] = None
            if state["rect"] is not None:
                canvas.delete(state["rect"])
            x, y = state["start"]
            state["rect"] = canvas.create_rectangle(
                x, y, x, y, outline="red", width=2
            )

        def move(event):
            if state["start"] is None:
                return
            x, y = coords(event)
            x0, y0 = state["start"]
            canvas.coords(state["rect"], x0, y0, x, y)

        def release(event):
            if state["start"] is None:
                return
            x0, y0 = state["start"]
            x1, y1 = coords(event)
            state["bounds"] = (
                min(x0, x1), min(y0, y1),
                max(x0, x1), max(y0, y1),
            )
            state["start"] = None

        canvas.bind("<ButtonPress-1>", press)
        canvas.bind("<B1-Motion>", move)
        canvas.bind("<ButtonRelease-1>", release)

        def confirm():
            bounds = state["bounds"]
            if bounds is None or bounds[2] - bounds[0] < 15 or bounds[3] - bounds[1] < 15:
                messagebox.showwarning("Selection", "Select a larger region of the object.", parent=window)
                return
            sx = image.shape[1] / display_w
            sy = image.shape[0] / display_h
            x1 = max(0, int(bounds[0] * sx))
            y1 = max(0, int(bounds[1] * sy))
            x2 = min(image.shape[1], int(np.ceil(bounds[2] * sx)))
            y2 = min(image.shape[0], int(np.ceil(bounds[3] * sy)))
            crop = image[y1:y2, x1:x2].copy()
            window.destroy()
            callback(crop)

        buttons = tk.Frame(window)
        buttons.pack(pady=8)
        tk.Button(buttons, text="Confirm", command=confirm, width=15).pack(side="left", padx=8)
        tk.Button(buttons, text="Cancel", command=window.destroy, width=15).pack(side="left")

    def _outline_object(self, image, callback):
        window = tk.Toplevel(self.root)
        self._roi_window = window
        window.title("Outline the object")
        window.transient(self.root)
        ttk.Label(window, text="Click around the object to mark its outline, then confirm.").pack(pady=5)
        photo = self._photo(image, (1100, 650))
        width, height = photo.width(), photo.height()
        canvas = tk.Canvas(window, width=width, height=height, cursor="crosshair", highlightthickness=0)
        canvas.pack()
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo
        vertices = []

        def add_point(event):
            vertices.append((event.x, event.y))
            canvas.delete("outline")
            if len(vertices) > 1:
                canvas.create_line(*vertices, vertices[0], fill="cyan", width=2, tags="outline")
            for x, y in vertices:
                canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="cyan", tags="outline")

        def clear():
            vertices.clear()
            canvas.delete("outline")

        def confirm():
            points = np.array([
                (int(x * image.shape[1] / width), int(y * image.shape[0] / height))
                for x, y in vertices
            ], dtype=np.int32)
            if len(points) < 3 or cv2.contourArea(points) < 10:
                messagebox.showwarning("Outline", "Mark at least three points around the object.", parent=window)
                return
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [points], 255)
            window.destroy()
            callback(mask)

        canvas.bind("<Button-1>", add_point)
        buttons = ttk.Frame(window)
        buttons.pack(pady=8)
        ttk.Button(buttons, text="Confirm", command=confirm).pack(side="left", padx=4)
        ttk.Button(buttons, text="Clear", command=clear).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="left", padx=4)

    def show_comparison(self, first_crop, second_crop, first_mask, second_mask, *, full_images=False):
        masks = (first_mask, second_mask)
        try:
            baseline_result, baseline_visual = compare_objects(first_crop, second_crop, object_masks=masks)
        except (cv2.error, ValueError) as exc:
            messagebox.showerror("Matching error", str(exc))
            return

        if self.comparison_window is not None and self.comparison_window.winfo_exists():
            self.comparison_window.destroy()
        win = tk.Toplevel(self.root)
        self.comparison_window = win
        scope = "Full images" if full_images else "Outlined regions"
        win.title(f"{scope} · SIFT + RANSAC comparison")
        panels = tk.Frame(win)
        panels.pack(padx=8, pady=8, fill="both", expand=True)
        panels.columnconfigure((0, 1), weight=1, uniform="comparison")
        baseline = tk.LabelFrame(panels, text="Baseline")
        baseline.grid(row=0, column=0, padx=4, sticky="nsew")
        processed = tk.LabelFrame(panels, text="With preprocessing")
        processed.grid(row=0, column=1, padx=4, sticky="nsew")
        max_size = (
            min(600, int(win.winfo_screenwidth() * 0.44)),
            min(450, int(win.winfo_screenheight() * 0.52)),
        )
        self._show_comparison_result(
            baseline, (0, 1.0, 1), baseline_result, baseline_visual, max_size,
            full_images=full_images,
        )

        def evaluate(channel, use_clahe, parameters):
            first = prepare_comparison_channel(first_crop, channel, parameters, clahe=use_clahe)
            second = prepare_comparison_channel(second_crop, channel, parameters, clahe=use_clahe)
            return compare_objects(
                first, second, object_masks=masks, display_images=(first_crop, second_crop)
            )

        def show_processed(channel, use_clahe, parameters, result, visual):
            for widget in processed.winfo_children():
                widget.destroy()
            self._show_comparison_result(
                processed, parameters, result, visual, max_size,
                channel=channel, clahe=use_clahe, full_images=full_images,
            )

        def rerun_comparison():
            channel = self.matching_channel.get()
            use_clahe = self.clahe.get()
            parameters = self.processing_parameters()
            try:
                result, visual = evaluate(channel, use_clahe, parameters)
            except (cv2.error, ValueError) as exc:
                messagebox.showerror("Matching error", str(exc), parent=win)
                return
            show_processed(channel, use_clahe, parameters, result, visual)

        def try_preprocessing():
            brightness, contrast, current_kernel = self.processing_parameters()
            kernels = sorted({1, 3, 5, current_kernel})
            best_rank = (-1.0, 0)
            best = None
            win.configure(cursor="watch")
            win.update_idletasks()
            try:
                for channel, use_clahe, kernel in product(MATCHING_CHANNELS, (False, True), kernels):
                    parameters = (brightness, contrast, kernel)
                    result, visual = evaluate(channel, use_clahe, parameters)
                    score = result["identification_ratio"]
                    if score is None:
                        continue
                    rank = (score, result["object_inliers"])
                    if rank > best_rank:
                        best_rank = rank
                        best = (channel, use_clahe, parameters, result, visual)
            except (cv2.error, ValueError) as exc:
                messagebox.showerror("Matching error", str(exc), parent=win)
                return
            finally:
                win.configure(cursor="")
            if best is None:
                messagebox.showinfo(
                    "Preprocessing", "No tested settings produced a valid comparison.", parent=win
                )
                return
            channel, use_clahe, parameters, result, visual = best
            self.matching_channel.set(channel)
            self.clahe.set(use_clahe)
            self._set_processing_parameters(*parameters)
            show_processed(channel, use_clahe, parameters, result, visual)

        win.bind("<<ComparisonConfigLoaded>>", lambda _: rerun_comparison())

        tk.Label(
            win, text="Adjust the sliders in the main window, then rerun on the same regions."
        ).pack(padx=8, pady=(0, 4))
        buttons = tk.Frame(win)
        buttons.pack(pady=(0, 10))
        ttk.Label(buttons, text="SIFT channel").pack(side="left", padx=4)
        matching_channel = ttk.Combobox(
            buttons, textvariable=self.matching_channel, values=MATCHING_CHANNELS,
            state="readonly", width=21,
        )
        matching_channel.pack(side="left", padx=4)
        matching_channel.bind("<<ComboboxSelected>>", lambda _: rerun_comparison())
        ttk.Checkbutton(buttons, text="CLAHE", variable=self.clahe,
                        command=rerun_comparison).pack(side="left", padx=4)
        ttk.Button(buttons, text="Load config", command=lambda: self._load_comparison_config(win)).pack(
            side="left", padx=4
        )
        tk.Button(buttons, text="Rerun comparison", command=rerun_comparison).pack(
            side="left", padx=4
        )
        ttk.Button(buttons, text="Try preprocessing", command=try_preprocessing).pack(
            side="left", padx=4
        )
        tk.Button(buttons, text="Close", command=win.destroy).pack(side="left", padx=4)
        rerun_comparison()

    def _show_comparison_result(self, panel, parameters, result, visual, max_size, *,
                                channel=GRAYSCALE, clahe=False, full_images=False):
        brightness, contrast, kernel_size = parameters
        settings = (
            f"{channel} · Brightness {brightness:+d} · Contrast {contrast:.1f}\n"
            f"Gaussian kernel {kernel_size} × {kernel_size} · CLAHE {'on' if clahe else 'off'}"
        )
        score = result["identification_ratio"]
        percentage = "N/A" if score is None else f"{score:.2%}"
        target_status = ""
        if score is not None:
            target_status = " · reached" if score >= 0.90 else " · below target"
        inlier_label = "Full-frame inliers" if full_images else "Object inliers"
        summary = (
            f"Keypoints: {result['keypoints1']} / {result['keypoints2']}\n"
            f"Good matches: {result['good_matches']}    "
            f"RANSAC inliers: {result['inliers']}\n"
            f"Inlier ratio: {result['inlier_ratio']:.1%}\n"
            f"{inlier_label} / candidate matches: {result['object_inliers']} / "
            f"{result['good_matches']} ({percentage}, target 90%{target_status})"
        )
        tk.Label(panel, text=settings, justify="center").pack(padx=8, pady=(8, 4))
        tk.Label(panel, text=summary, justify="center").pack(padx=8, pady=4)
        if visual is not None:
            photo = self._photo(visual, max_size)
            label = tk.Label(panel, image=photo)
            label.image = photo
            label.pack(padx=8, pady=5)
        else:
            tk.Label(panel, text="Too few SIFT keypoints. Try a larger, clearer crop.").pack(
                padx=8, pady=8
            )
        print(f"SIFT + RANSAC [{panel.cget('text')}]",
              f"channel={channel}, CLAHE={clahe}, brightness={brightness}, "
              f"contrast={contrast:.1f}, kernel={kernel_size}",
              result)
