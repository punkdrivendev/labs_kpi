from pathlib import Path
from PIL import Image
import numpy as np


def load_image(path):
    with Image.open(path) as image:
        return np.array(image.convert("RGB"), dtype=np.uint8)


def load_images(image_dest="images/"):
    image_dir = Path(image_dest)

    if not image_dir.exists():
        raise FileNotFoundError(
            f"Directory does not exist: {image_dir.resolve()}"
        )

    supported = {".jpg", ".jpeg", ".png"}

    image_files = sorted(
        file
        for file in image_dir.iterdir()
        if file.is_file()
        and file.suffix.lower() in supported
    )

    if not image_files:
        raise RuntimeError(
            f"No images found in: {image_dir.resolve()}"
        )

    images = []

    for image_path in image_files:
        img_array = load_image(image_path)
        images.append(img_array)

        print(
            f"Loaded: {image_path.name}, "
            f"shape={img_array.shape}, "
            f"dtype={img_array.dtype}"
        )

    return images
