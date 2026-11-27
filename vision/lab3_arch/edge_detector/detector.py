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


def compare_objects(image1, image2, nfeatures=3000, ratio_threshold=0.80):
    gray1 = prepare_for_matching(image1)
    gray2 = prepare_for_matching(image2)

    sift = cv2.SIFT_create(
        nfeatures=3000,
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

    shown = [m for m, keep in zip(good, mask) if keep] if mask is not None else good
    shown = shown[:60]
    visualization_bgr = cv2.drawMatches(
        gray1, kp1, gray2, kp2, shown, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )
    visualization_rgb = cv2.cvtColor(visualization_bgr, cv2.COLOR_BGR2RGB)
    return result, visualization_rgb
