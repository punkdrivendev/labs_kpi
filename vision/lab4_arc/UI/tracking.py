"""Playback, target selection and results for the Lab 4 tracking experiment."""

import tkinter as tk
from pathlib import Path
from time import perf_counter
from tkinter import filedialog, messagebox, simpledialog, ttk

import cv2
from PIL import Image, ImageTk

from video_tracking.experiment import TrackingExperiment, load_reference_boxes
from video_tracking.trackers import TRACKERS


COLORS = ("#38dfff", "#fdce48", "#ff75cd")


class TrackingWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Lab 4 · Object Tracking")
        self.capture = None
        self.timer = None
        self.frame = None
        self.frame_number = 0
        self.box = None
        self.drag_start = None
        self.experiment = None
        self.reference = {}
        self.source = ""
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Destroy>", self._on_destroy)

        body = ttk.Frame(self, padding=10)
        body.pack(fill="both", expand=True)
        controls = ttk.Frame(body)
        controls.pack(fill="x")
        ttk.Button(controls, text="Open video", command=self._open_file).pack(side="left")
        ttk.Button(controls, text="Camera", command=self._open_camera).pack(side="left", padx=(4, 0))
        self.reference_button = ttk.Button(controls, text="Reference CSV", command=self._open_reference, state="disabled")
        self.reference_button.pack(side="left", padx=4)
        self.start_button = ttk.Button(controls, text="Start tracking", command=self._start, state="disabled")
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop", command=self._stop, state="disabled")
        self.stop_button.pack(side="left", padx=4)
        self.export_button = ttk.Button(controls, text="Export CSV", command=self._export, state="disabled")
        self.export_button.pack(side="left")

        self.status = tk.StringVar(self, value="Open a video or camera and select an object in the first frame.")
        ttk.Label(body, textvariable=self.status, wraplength=650).pack(anchor="w", pady=6)
        self.canvas = tk.Canvas(body, width=640, height=320, highlightthickness=0, background="#151515")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self._begin_selection)
        self.canvas.bind("<B1-Motion>", self._draw_selection)
        self.canvas.bind("<ButtonRelease-1>", self._end_selection)

        columns = ("method", "boxes", "mean_ms", "iou")
        self.table = ttk.Treeview(body, columns=columns, show="headings", height=len(TRACKERS))
        for key, label, width in zip(
            columns, ("Method", "Boxes / frames", "Mean ms / frame", "Mean IoU (frames)"), (165, 105, 125, 145)
        ):
            self.table.heading(key, text=label)
            self.table.column(key, width=width, stretch=True)
        for tracker, color in zip(TRACKERS, COLORS):
            self.table.insert("", "end", iid=tracker.name, values=(tracker.name, "—", "—", "—"), tags=(color,))
            self.table.tag_configure(color, background=color, foreground="#171717")
        self.table.pack(fill="x", pady=(8, 0))

    def _open_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All files", "*.*")],
        )
        if path:
            self._open(path, Path(path).name)

    def _open_camera(self):
        index = simpledialog.askinteger("Camera", "Device index", initialvalue=0, minvalue=0, parent=self)
        if index is not None:
            self._open(index, f"Camera {index}")

    def _open(self, source, label):
        self._stop()
        capture = cv2.VideoCapture(source)
        ready, frame = capture.read() if capture.isOpened() else (False, None)
        if not ready:
            capture.release()
            messagebox.showerror("Video source", "Could not read the first frame.", parent=self)
            return
        self.capture = capture
        fps = capture.get(cv2.CAP_PROP_FPS)
        self.frame_interval = 1 / fps if 1 <= fps <= 240 else 1 / 30
        self.source = label
        self.frame = frame
        self.frame_number = 0
        self.box = None
        self.drag_start = None
        self.experiment = None
        self.reference = {}
        self.export_button.configure(state="disabled")
        self.reference_button.configure(state="normal")
        self.status.set(f"{label} · Drag a box around one object in frame 0.")
        self._refresh_table()
        self._render()

    def _open_reference(self):
        path = filedialog.askopenfilename(
            parent=self, title="Reference boxes (frame,x,y,width,height)", filetypes=[("CSV", "*.csv")]
        )
        if path:
            try:
                self.reference = load_reference_boxes(path)
            except (OSError, ValueError) as exc:
                messagebox.showerror("Reference CSV", str(exc), parent=self)
                return
            self.status.set(f"{self.source} · {len(self.reference)} reference boxes loaded. Frame numbers start at 0.")

    def _begin_selection(self, event):
        if self.capture is not None and self.experiment is None:
            self.drag_start = self._canvas_point(event)

    def _draw_selection(self, event):
        if self.drag_start is not None:
            self.canvas.delete("selection")
            self.canvas.create_rectangle(
                *self.drag_start, *self._canvas_point(event), outline="white", width=2, tags="selection"
            )

    def _canvas_point(self, event):
        return min(max(0, event.x), self.photo.width()), min(max(0, event.y), self.photo.height())

    def _end_selection(self, event):
        if self.drag_start is None:
            return
        self._draw_selection(event)
        x, y = self._canvas_point(event)
        x0, y0 = self.drag_start
        self.drag_start = None
        width, height = self.frame.shape[1], self.frame.shape[0]
        left, right = sorted((x * width // self.photo.width(), x0 * width // self.photo.width()))
        top, bottom = sorted((y * height // self.photo.height(), y0 * height // self.photo.height()))
        self.box = (left, top, right - left, bottom - top)
        valid = min(self.box[2:]) >= 8
        self.start_button.configure(state="normal" if valid else "disabled")
        self.status.set("Target selected. Click Start tracking." if valid else "Select a box of at least 8 × 8 pixels.")

    def _start(self):
        if self.capture is None or self.box is None or min(self.box[2:]) < 8:
            return
        try:
            self.experiment = TrackingExperiment(self.frame, self.box, self.reference)
        except cv2.error as exc:
            messagebox.showerror("Object Tracking", str(exc), parent=self)
            return
        self.start_button.configure(state="disabled")
        self.reference_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.timer = self.after(0, self._step)

    def _step(self):
        self.timer = None
        start = perf_counter()
        try:
            ready, frame = self.capture.read()
            if not ready:
                self._stop("Video ended or no more frames are available.")
                return
            self.frame_number += 1
            boxes = self.experiment.update(self.frame_number, frame)
        except cv2.error as exc:
            self._stop("Tracking stopped.")
            messagebox.showerror("Object Tracking", str(exc), parent=self)
            return
        self.frame = frame
        self._render(boxes)
        self._refresh_table()
        self.status.set(f"{self.source} · Frame {self.frame_number} · Frame 0 used for initialization")
        self.export_button.configure(state="normal")
        delay = max(1, int(1000 * (self.frame_interval - (perf_counter() - start))))
        self.timer = self.after(delay, self._step)

    def _render(self, boxes=()):
        image = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
        image.thumbnail((min(960, int(self.winfo_screenwidth() * 0.9)), min(520, int(self.winfo_screenheight() * 0.64))))
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.configure(width=image.width, height=image.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        scale_x = image.width / self.frame.shape[1]
        scale_y = image.height / self.frame.shape[0]
        for box, color in zip(boxes, COLORS):
            if box is not None:
                x, y, width, height = box
                self.canvas.create_rectangle(
                    x * scale_x, y * scale_y, (x + width) * scale_x, (y + height) * scale_y,
                    outline=color, width=2,
                )

    def _refresh_table(self):
        for tracker in TRACKERS:
            summary = self.experiment.summary[tracker.name] if self.experiment else None
            if summary is not None and summary.frames:
                coverage = f"{summary.tracked}/{summary.frames} ({summary.tracked / summary.frames:.0%})"
                mean_ms = f"{summary.update_ms / summary.frames:.2f}"
                iou = (f"{summary.iou_sum / summary.reference_frames:.2f} ({summary.reference_frames})"
                       if summary.reference_frames else "—")
                values = (tracker.name, coverage, mean_ms, iou)
            else:
                values = (tracker.name, "—", "—", "—")
            self.table.item(tracker.name, values=values)

    def _export(self):
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile="lab4-tracking.csv",
        )
        if path:
            try:
                self.experiment.export_csv(path, self.source)
            except OSError as exc:
                messagebox.showerror("Export CSV", str(exc), parent=self)

    def _stop(self, message="Tracking stopped. Open a source to start a new run."):
        self._release_source()
        self.start_button.configure(state="disabled")
        self.reference_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.status.set(message)

    def _release_source(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.drag_start = None

    def _on_destroy(self, event):
        if event.widget is self:
            self._release_source()
