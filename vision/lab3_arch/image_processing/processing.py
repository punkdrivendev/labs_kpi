import cv2
import numpy as np


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
