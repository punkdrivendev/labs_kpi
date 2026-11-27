import cv2
import numpy as np


def detect_edges(image, param1=110, param2=220):
    gray = prepare_for_matching(image)
    return cv2.Canny(gray, param1, param2, L2gradient=True)


def prepare_for_matching(image):
    if image is None or image.size == 0:
        raise ValueError("Image is empty")
    if image.ndim == 3:
        if image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    elif image.ndim == 2:
        gray = image
    else:
        raise ValueError("Expected RGB or grayscale image")
    return np.clip(gray, 0, 255).astype(np.uint8)


def compare_objects(image1, image2, nfeatures=3000, ratio_threshold=0.80, *,
                    object_masks=None, display_images=None):
    gray1 = prepare_for_matching(image1)
    gray2 = prepare_for_matching(image2)

    sift = cv2.SIFT_create(
        nfeatures=nfeatures,
        contrastThreshold=0.02,
        edgeThreshold=15
    )

    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    result = {
        "keypoints1": len(kp1),
        "keypoints2": len(kp2),
        "good_matches": 0,
        "inliers": 0,
        "inlier_ratio": 0.0,
        "same_object": False,
        "object_inliers": 0,
        "identification_ratio": None,
    }

    if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
        return result, None

    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    pairs = matcher.knnMatch(des1, des2, k=2)
    good = [m for pair in pairs if len(pair) == 2
            for m, n in [pair] if m.distance < ratio_threshold * n.distance]
    good.sort(key=lambda match: match.distance)
    result["good_matches"] = len(good)

    mask = None
    if len(good) >= 4:
        source = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        target = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        try:
            homography, inlier_mask = cv2.findHomography(
                source, target, cv2.RANSAC, 5.0
            )
        except cv2.error:
            homography, inlier_mask = None, None
        if homography is not None and inlier_mask is not None:
            mask = inlier_mask.ravel().astype(bool)
            inliers = int(mask.sum())
            result["inliers"] = inliers
            result["inlier_ratio"] = inliers / len(good)
            result["same_object"] = (inliers >= 10 and result["inlier_ratio"] >= 0.5)
            if object_masks is not None:
                first_mask, second_mask = object_masks
                first_pixels = source[:, 0].astype(int)
                second_pixels = target[:, 0].astype(int)
                on_object = (
                    (first_mask[first_pixels[:, 1], first_pixels[:, 0]] != 0)
                    & (second_mask[second_pixels[:, 1], second_pixels[:, 0]] != 0)
                )
                mask &= on_object
                result["object_inliers"] = int(mask.sum())
                result["identification_ratio"] = result["object_inliers"] / len(good)

    shown = [m for m, keep in zip(good, mask) if keep] if mask is not None else []
    shown = shown[:60]
    preview1, preview2 = display_images if display_images is not None else (image1, image2)
    visualization_bgr = cv2.drawMatches(
        _match_preview(preview1), kp1, _match_preview(preview2), kp2, shown, None,
        matchColor=(0, 255, 255),
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )
    visualization_rgb = cv2.cvtColor(visualization_bgr, cv2.COLOR_BGR2RGB)
    return result, visualization_rgb


def _match_preview(image):
    if image.ndim == 3:
        conversion = cv2.COLOR_RGBA2BGR if image.shape[2] == 4 else cv2.COLOR_RGB2BGR
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        return cv2.cvtColor(image, conversion)
    return prepare_for_matching(image)
