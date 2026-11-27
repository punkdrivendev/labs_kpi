"""Tkinter interface for image comparison and building detection."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from UI.detection import DetectionControls, show_detection_result
from edge_detector.buildings import HSV_SEGMENTATION, DetectionSettings, detect_buildings
from edge_detector.detection_config import load_config, save_config
from edge_detector.road_zones import draw_road_separators
from image_loader.loader import load_image
from image_processing.processing import image_to_grey, preprocess_image
from edge_detector.detector import detect_edges, compare_objects


IMAGE_COMPARISON = "Image Comparison"
OBJECT_DETECTION = "Object Detection"
PREPROCESSING_DEFAULTS = {
    IMAGE_COMPARISON: (0, 1.0, 1),
    OBJECT_DETECTION: DetectionSettings().preprocessing,
}
IMAGE_TYPES = [
    ("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff"),
    ("All files", "*.*"),
]


class ImageUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processing")
        self.root.minsize(520, 1)

        self.original_image = None
        self.second_image = None
        self.detection_image = None
        self.road_barriers = None
        self.road_editor = None
        self.gray_image = None
        self.current_image = None
        self.image_window = None
        self.image_label = None
        self.stage = None
        self._roi_window = None
        self.comparison_window = None
        self.detection_window = None
        self.active_mode = IMAGE_COMPARISON
        self.mode_parameters = PREPROCESSING_DEFAULTS.copy()

        body = ttk.Frame(root, padding=10)
        body.pack(fill="both", expand=True)
        mode_row = ttk.Frame(body)
        mode_row.pack(fill="x", pady=(0, 8))
        ttk.Label(mode_row, text="Mode").pack(side="left", padx=(0, 8))
        self.mode = tk.StringVar(root, IMAGE_COMPARISON)
        ttk.Combobox(
            mode_row, textvariable=self.mode, values=(IMAGE_COMPARISON, OBJECT_DETECTION),
            state="readonly", width=21
        ).pack(side="left")

        inputs = ttk.Frame(body)
        inputs.pack(fill="x")
        self.comparison_inputs = ttk.Frame(inputs)
        ttk.Button(self.comparison_inputs, text="Select first image",
                   command=self.select_image).grid(row=0, column=0, padx=(0, 6), pady=2, sticky="ew")
        ttk.Button(self.comparison_inputs, text="Select second image",
                   command=self.select_second_image).grid(row=1, column=0, padx=(0, 6), pady=2, sticky="ew")
        self.file_label = ttk.Label(self.comparison_inputs, text="No image selected", wraplength=350)
        self.file_label.grid(row=0, column=1, sticky="w")
        self.second_file_label = ttk.Label(self.comparison_inputs, text="No image selected", wraplength=350)
        self.second_file_label.grid(row=1, column=1, sticky="w")

        self.detection_inputs = ttk.Frame(inputs)
        ttk.Button(self.detection_inputs, text="Select map image",
                   command=self.select_detection_image).pack(side="left", padx=(0, 6))
        self.detection_file_label = ttk.Label(
            self.detection_inputs, text="No image selected", wraplength=350
        )
        self.detection_file_label.pack(side="left")

        preprocessing_area = ttk.Frame(body)
        preprocessing_area.pack(fill="x")
        self.preprocessing = ttk.LabelFrame(preprocessing_area, text="Preprocessing")
        self.preprocessing.columnconfigure(1, weight=1)
        ttk.Label(self.preprocessing, text="Brightness").grid(row=0, column=0, sticky="w", padx=6)
        self.brightness_slider = tk.Scale(
            self.preprocessing, from_=-255, to=255, orient=tk.HORIZONTAL,
            length=280, showvalue=False, command=self.update_processing
        )
        self.brightness_slider.set(0)
        self.brightness_slider.grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Label(self.preprocessing, text="Contrast").grid(row=1, column=0, sticky="w", padx=6)
        self.contrast_slider = tk.Scale(
            self.preprocessing, from_=0.1, to=3.0, resolution=0.1,
            orient=tk.HORIZONTAL, length=280, showvalue=False, command=self.update_processing
        )
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, sticky="ew", padx=6)

        ttk.Label(self.preprocessing, text="Gaussian blur").grid(row=2, column=0, sticky="w", padx=6)
        self.blur_slider = tk.Scale(
            self.preprocessing, from_=0, to=10, orient=tk.HORIZONTAL, showvalue=False,
            length=280, command=self.update_processing
        )
        self.blur_slider.set(0)
        self.blur_slider.grid(row=2, column=1, sticky="ew", padx=6)

        self.values_label = ttk.Label(self.preprocessing)
        self.values_label.grid(row=3, column=0, columnspan=2, padx=6, pady=4, sticky="w")
        ttk.Button(self.preprocessing, text="Reset", command=self.reset_parameters).grid(
            row=3, column=2, padx=6, pady=4
        )
        self.update_values_label()

        actions = ttk.Frame(body)
        actions.pack(fill="x")
        self.comparison_actions = ttk.Frame(actions)
        self.compare_button = ttk.Button(
            self.comparison_actions, text="Compare regions",
            command=self.start_comparison, state="disabled"
        )
        self.compare_button.pack(anchor="w", pady=(4, 0))
        ttk.Label(
            self.comparison_actions, text="Select regions for SIFT + RANSAC. Close the image preview "
            "to step through the original, preprocessing and Canny views.", wraplength=470
        ).pack(anchor="w", pady=(5, 0))

        self.detection_actions = ttk.Frame(actions)
        self.detection_controls = DetectionControls(
            self.detection_actions, self.edit_road_separators
        )
        self.detection_controls.pack(fill="x")
        detection_buttons = ttk.Frame(self.detection_actions)
        detection_buttons.pack(fill="x", pady=(4, 0))
        self.detect_button = ttk.Button(
            detection_buttons, text="Detect buildings", command=self.run_detection, state="disabled"
        )
        self.detect_button.pack(side="left")
        ttk.Button(detection_buttons, text="Load JSON", command=self.load_detection_config).pack(
            side="left", padx=6
        )
        ttk.Button(detection_buttons, text="Save JSON", command=self.save_detection_config).pack(
            side="left"
        )

        ttk.Button(body, text="Finish", command=self.finish).pack(anchor="e", pady=(8, 0))
        self.mode.trace_add("write", self.update_mode)
        self.update_mode()

    def _update_preprocessing_visibility(self):
        if self.mode.get() == IMAGE_COMPARISON:
            self.preprocessing.pack(fill="x", pady=6)
        else:
            self.preprocessing.pack_forget()

    def update_mode(self, *_):
        mode = self.mode.get()
        if mode != self.active_mode:
            self.mode_parameters[self.active_mode] = self.processing_parameters()
            self.active_mode = mode
        self._close_stage_window()
        self.stage = None
        for window in (self._roi_window, self.comparison_window, self.detection_window, self.road_editor):
            if window is not None and window.winfo_exists():
                window.destroy()
        if mode == IMAGE_COMPARISON:
            self.detection_inputs.pack_forget()
            self.detection_actions.pack_forget()
            self.comparison_inputs.pack(fill="x")
            self.comparison_actions.pack(fill="x")
        else:
            self.comparison_inputs.pack_forget()
            self.comparison_actions.pack_forget()
            self.detection_inputs.pack(fill="x")
            self.detection_actions.pack(fill="x")
        self._set_processing_parameters(self.mode_parameters[mode])
        self._update_preprocessing_visibility()

    def _choose_image(self, title):
        path = filedialog.askopenfilename(parent=self.root, title=title, filetypes=IMAGE_TYPES)
        if not path:
            return None
        try:
            return load_image(path), Path(path).name
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            messagebox.showerror("Image error", str(exc), parent=self.root)
            return None

    def select_image(self):
        selection = self._choose_image("Select first image")
        if selection is None:
            return
        rgb, name = selection
        self.original_image = rgb
        self.gray_image = image_to_grey(rgb)
        self.file_label.config(text=name)
        self._enable_comparison()
        self.stage = "original"
        self.update_processing()
        self.open_image_window(rgb, "Original image")

    def select_second_image(self):
        selection = self._choose_image("Select second image")
        if selection is not None:
            self.second_image, name = selection
            self.second_file_label.config(text=name)
            self._enable_comparison()

    def _enable_comparison(self):
        if self.original_image is not None and self.second_image is not None:
            self.compare_button.configure(state="normal")

    def select_detection_image(self):
        selection = self._choose_image("Select map image")
        if selection is not None:
            self.detection_image, name = selection
            self.road_barriers = None
            if self.road_editor is not None and self.road_editor.winfo_exists():
                self.road_editor.destroy()
            self.detection_file_label.config(text=name)
            self.detect_button.configure(state="normal")
            if self.detection_window is not None and self.detection_window.winfo_exists():
                self.detection_window.destroy()

    def run_detection(self):
        if self.detection_image is None:
            return
        method = HSV_SEGMENTATION
        try:
            settings = self.detection_controls.settings()
            result = detect_buildings(self.detection_image, method, settings, self.road_barriers)
        except (cv2.error, ValueError) as exc:
            messagebox.showerror("Detection error", str(exc), parent=self.root)
            return
        if self.detection_window is not None and self.detection_window.winfo_exists():
            self.detection_window.destroy()
        self.detection_window = show_detection_result(self.root, method, result, self._photo)

    def edit_road_separators(self):
        if self.detection_image is None:
            messagebox.showinfo("Road zones", "Select a map image first.", parent=self.root)
            return
        if self.road_editor is not None and self.road_editor.winfo_exists():
            self.road_editor.lift()
            return

        image = self.detection_image
        height, width = image.shape[:2]
        draft = self.road_barriers.copy() if self.road_barriers is not None else draw_road_separators(
            (height, width), self.detection_controls.road_separators
        )
        window = tk.Toplevel(self.root)
        self.road_editor = window
        window.title("Draw road separators")
        window.transient(self.root)
        limit = (int(window.winfo_screenwidth() * 0.88), int(window.winfo_screenheight() * 0.78))
        pil = Image.fromarray(image)
        pil.thumbnail(limit)
        display_w, display_h = pil.size
        ttk.Label(
            window, text="Click along a road to connect it to another separator or the image edge. "
                         "Right-click to end the chain.",
            wraplength=640
        ).pack(pady=5)
        preview = tk.Canvas(window, width=display_w, height=display_h, highlightthickness=0)
        preview.pack()
        image_item = preview.create_image(0, 0, anchor="nw")
        previous = None

        def redraw():
            overlay = image.copy()
            overlay[draft != 0] = (255, 90, 30)
            photo = self._photo(overlay, (display_w, display_h))
            preview.itemconfigure(image_item, image=photo)
            preview.image = photo

        def end_chain(_=None):
            nonlocal previous
            previous = None
            preview.delete("point")

        def add_point(event):
            nonlocal previous
            x = min(width - 1, max(0, round(event.x * width / display_w)))
            y = min(height - 1, max(0, round(event.y * height / display_h)))
            if previous is not None:
                cv2.line(draft, previous, (x, y), 255, 9)
                redraw()
            previous = (x, y)
            preview.delete("point")
            preview.create_oval(event.x-3, event.y-3, event.x+3, event.y+3, fill="#ff5a1e", tags="point")

        def clear():
            draft.fill(0)
            end_chain()
            redraw()

        def apply():
            self.road_barriers = draft
            window.destroy()

        preview.bind("<Button-1>", add_point)
        preview.bind("<Button-3>", end_chain)
        buttons = ttk.Frame(window)
        buttons.pack(pady=6)
        ttk.Button(buttons, text="Clear", command=clear).pack(side="left", padx=4)
        ttk.Button(buttons, text="Apply separators", command=apply).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="left", padx=4)
        redraw()

    def load_detection_config(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Load detection settings", filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            method, settings = load_config(path)
            if method != HSV_SEGMENTATION:
                raise ValueError("Choose an HSV Segmentation preset.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Configuration error", str(exc), parent=self.root)
            return
        self.detection_controls.apply_settings(settings)
        self.road_barriers = None
        if self.road_editor is not None and self.road_editor.winfo_exists():
            self.road_editor.destroy()

    def save_detection_config(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Save detection settings", defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            method = HSV_SEGMENTATION
            settings = self.detection_controls.settings(include_inactive=True)
            save_config(path, method, settings)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Configuration error", str(exc), parent=self.root)

    def reset_parameters(self):
        self._set_processing_parameters(PREPROCESSING_DEFAULTS[self.mode.get()])

    def _set_processing_parameters(self, parameters):
        brightness, contrast, kernel_size = parameters
        self.brightness_slider.set(brightness)
        self.contrast_slider.set(contrast)
        self.blur_slider.set((kernel_size - 1) // 2)
        self.update_processing()

    def update_processing(self, _=None):
        self.update_values_label()
        if self.mode.get() != IMAGE_COMPARISON or self.gray_image is None:
            return
        self.current_image = preprocess_image(self.gray_image, *self.processing_parameters())
        if self.stage == "preprocessing" and self.image_label is not None:
            self.update_image_label(self.current_image)

    def processing_parameters(self):
        # Each slider step selects the next odd Gaussian kernel.
        kernel_size = 2 * self.blur_slider.get() + 1
        return (
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            kernel_size,
        )

    def update_values_label(self):
        brightness, contrast, kernel_size = self.processing_parameters()
        self.values_label.config(
            text=f"Brightness: {brightness}    "
                 f"Contrast: {contrast:.1f}    "
                 f"Gaussian kernel: {kernel_size} × {kernel_size}"
        )

    def finish(self):
        self.root.destroy()

    @staticmethod
    def _photo(image, max_size=(1200, 800)):
        pil = Image.fromarray(np.clip(image, 0, 255).astype(np.uint8))
        pil.thumbnail(max_size)
        return ImageTk.PhotoImage(pil)

    def open_image_window(self, image, title):
        if self.image_window is not None and self.image_window.winfo_exists():
            self.image_window.destroy()
        self.image_window = tk.Toplevel(self.root)
        self.image_window.title(title)
        self.image_label = tk.Label(self.image_window)
        self.image_label.pack()
        self.update_image_label(image)
        self.image_window.protocol("WM_DELETE_WINDOW", self.close_image_window)

    def update_image_label(self, image):
        if self.image_label is None:
            return
        photo = self._photo(image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def _close_stage_window(self):
        if self.image_window is not None and self.image_window.winfo_exists():
            self.image_window.destroy()
        self.image_window = None
        self.image_label = None

    def close_image_window(self):
        if self.stage == "original":
            self._close_stage_window()
            self.stage = "preprocessing"
            self.update_processing()
            self.open_image_window(self.current_image, "Preprocessing")
        elif self.stage == "preprocessing":
            self._close_stage_window()
            edges = detect_edges(self.current_image, 110, 220)
            result = self.original_image.copy()
            result[edges > 0] = (255, 0, 0)
            self.stage = "canny"
            self.open_image_window(result, "Canny contours (red)")
        else:
            self._close_stage_window()
            self.stage = None

    def start_comparison(self):
        if self.original_image is None or self.second_image is None:
            return
        if self._roi_window is not None and self._roi_window.winfo_exists():
            self._roi_window.lift()
            return
        second_image = self.second_image
        self._select_region(
            self.original_image,
            "First image: drag a rectangle around the object",
            lambda first_crop: self._select_region(
                second_image,
                "Second image: select the corresponding or control region",
                lambda second_crop: self.show_comparison(first_crop, second_crop),
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
        tk.Label(window, text="Drag to select the building, then click Confirm").pack(pady=5)
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

    def show_comparison(self, first_crop, second_crop):
        try:
            baseline_result, baseline_visual = compare_objects(first_crop, second_crop)
        except (cv2.error, ValueError) as exc:
            messagebox.showerror("Matching error", str(exc))
            return

        if self.comparison_window is not None and self.comparison_window.winfo_exists():
            self.comparison_window.destroy()
        win = tk.Toplevel(self.root)
        self.comparison_window = win
        win.title("SIFT + RANSAC comparison")
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
            baseline, (0, 1.0, 1), baseline_result, baseline_visual, max_size
        )

        def rerun_comparison():
            parameters = self.processing_parameters()
            try:
                first = preprocess_image(first_crop, *parameters)
                second = preprocess_image(second_crop, *parameters)
                result, visual = compare_objects(first, second)
            except (cv2.error, ValueError) as exc:
                messagebox.showerror("Matching error", str(exc), parent=win)
                return

            for widget in processed.winfo_children():
                widget.destroy()
            self._show_comparison_result(processed, parameters, result, visual, max_size)

        tk.Label(
            win, text="Adjust the sliders in the main window, then rerun on the same regions."
        ).pack(padx=8, pady=(0, 4))
        buttons = tk.Frame(win)
        buttons.pack(pady=(0, 10))
        tk.Button(buttons, text="Rerun comparison", command=rerun_comparison).pack(
            side="left", padx=4
        )
        tk.Button(buttons, text="Close", command=win.destroy).pack(side="left", padx=4)
        rerun_comparison()

    def _show_comparison_result(self, panel, parameters, result, visual, max_size):
        brightness, contrast, kernel_size = parameters
        settings = (
            f"Grayscale · Brightness {brightness:+d} · Contrast {contrast:.1f}\n"
            f"Gaussian kernel {kernel_size} × {kernel_size}"
        )
        summary = (
            f"Keypoints: {result['keypoints1']} / {result['keypoints2']}\n"
            f"Good matches: {result['good_matches']}    "
            f"RANSAC inliers: {result['inliers']}\n"
            f"Inlier ratio: {result['inlier_ratio']:.1%}\n"
            f"Heuristic same-object decision: {result['same_object']}"
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
              f"brightness={brightness}, contrast={contrast:.1f}, kernel={kernel_size}",
              result)
