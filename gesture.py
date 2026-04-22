import math
from config import CLICK_PINCH_THRESHOLD


def _is_extended(landmarks, tip_idx, pip_idx):
    return landmarks[tip_idx].y < landmarks[pip_idx].y


def _is_curled(landmarks, tip_idx, pip_idx):
    return landmarks[tip_idx].y > landmarks[pip_idx].y


def classify_gesture(landmarks):
    if landmarks is None or len(landmarks) < 21:
        return "UNKNOWN"

    index_ext = _is_extended(landmarks, 8, 6)
    middle_ext = _is_extended(landmarks, 12, 10)
    ring_ext = _is_extended(landmarks, 16, 14)
    pinky_ext = _is_extended(landmarks, 20, 18)

    index_curled = _is_curled(landmarks, 8, 6)
    middle_curled = _is_curled(landmarks, 12, 10)
    ring_curled = _is_curled(landmarks, 16, 14)
    pinky_curled = _is_curled(landmarks, 20, 18)

    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_extended_up = thumb_tip.y < thumb_ip.y

    pinch_dist = math.dist(
        (landmarks[4].x, landmarks[4].y, landmarks[4].z),
        (landmarks[8].x, landmarks[8].y, landmarks[8].z),
    )
    if pinch_dist < CLICK_PINCH_THRESHOLD:
        return "PINCH"

    if index_ext and middle_ext and ring_ext and pinky_ext:
        return "OPEN"

    if thumb_extended_up and index_curled and middle_curled and ring_curled and pinky_curled:
        return "THUMBS_UP"

    if index_curled and middle_curled and ring_curled and pinky_curled:
        return "FIST"

    if index_ext and middle_curled and ring_curled and pinky_curled:
        return "POINT"

    if index_ext and middle_ext and ring_curled and pinky_curled:
        return "PEACE"

    if index_ext and middle_ext and ring_curled and pinky_curled:
        return "PEACE"

    return "UNKNOWN"
