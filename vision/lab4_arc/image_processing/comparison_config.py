"""Read settings for the Lab 4 comparison controls."""

import json

from image_processing.processing import MATCHING_CHANNELS


def load_comparison_config(path):
    with open(path, encoding="utf-8") as file:
        config = json.load(file)

    fields = {"channel", "clahe", "brightness", "contrast", "gaussian_kernel"}
    if not isinstance(config, dict) or config.keys() != fields:
        raise ValueError("Expected these settings: " + ", ".join(sorted(fields)))
    if config["channel"] not in MATCHING_CHANNELS:
        raise ValueError("Channel must be one of: " + ", ".join(MATCHING_CHANNELS))
    if type(config["clahe"]) is not bool:
        raise ValueError("CLAHE must be true or false.")

    brightness = config["brightness"]
    contrast = config["contrast"]
    kernel = config["gaussian_kernel"]
    if type(brightness) is not int or not -255 <= brightness <= 255:
        raise ValueError("Brightness must be an integer from -255 to 255.")
    if type(contrast) not in (int, float) or not 0.1 <= contrast <= 3 or contrast != round(contrast, 1):
        raise ValueError("Contrast must be from 0.1 to 3.0 in steps of 0.1.")
    if type(kernel) is not int or kernel not in range(1, 22, 2):
        raise ValueError("Gaussian kernel must be an odd integer from 1 to 21.")

    return config
