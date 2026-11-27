import cv2
import numpy as np


GRAYSCALE = "Grayscale"
HSV_VALUE = "HSV · Value (V)"
HSV_SATURATION = "HSV · Saturation (S)"
MATCHING_CHANNELS = (GRAYSCALE, HSV_VALUE, HSV_SATURATION)


def image_to_grey(image):
    return cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )


def negative_image(image_grey):
    return 255 - image_grey


def brightness_manip(image, factor):
    image = image.astype(
        np.float32
    )

    result = image + factor

    result = np.clip(
        result,
        0,
        255
    )

    return result.astype(
        np.uint8
    )


def contrast_manip(image, factor):
    image = image.astype(
        np.float32
    )

    result = (
        (image - 128)
        * factor
        + 128
    )

    result = np.clip(
        result,
        0,
        255
    )

    return result.astype(
        np.uint8
    )


def blur_image(image, kernel_size):
    if kernel_size < 1:
        kernel_size = 1

    if kernel_size % 2 == 0:
        kernel_size += 1

    return cv2.GaussianBlur(
        image,
        (kernel_size, kernel_size),
        0
    )


def preprocess_image(image, brightness=0, contrast=1.0, kernel_size=1):
    gray = image_to_grey(image) if image.ndim == 3 else image
    corrected = brightness_manip(gray, brightness)
    corrected = contrast_manip(corrected, contrast)
    return blur_image(corrected, kernel_size)


def apply_gabor(image):
    if image.ndim == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2GRAY
        )
    else:
        gray = image

    kernel = cv2.getGaborKernel(
        (21, 21),
        5,
        0,
        10,
        0.5,
        0
    )

    result = cv2.filter2D(
        gray,
        cv2.CV_32F,
        kernel
    )

    result = np.abs(result)

    result = cv2.normalize(
        result,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    return result.astype(np.uint8)


def correct_lightness(image):
    """Apply local contrast correction to the Lab lightness channel."""
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def prepare_comparison_channel(image, channel, parameters, *, clahe=False):
    """Prepare the selected channel for SIFT on a color comparison crop."""
    if channel == GRAYSCALE:
        corrected = correct_lightness(image) if clahe else image
        return preprocess_image(corrected, *parameters)

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    if channel == HSV_VALUE:
        values = hsv[:, :, 2]
    elif channel == HSV_SATURATION:
        values = hsv[:, :, 1]
    else:
        raise ValueError(f"Unknown comparison channel: {channel}")

    if clahe:
        values = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(values)
    return preprocess_image(values, *parameters)
