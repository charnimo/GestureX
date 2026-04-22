from collections import deque
import pyautogui
from config import (
    SMOOTH_FACTOR,
    DEAD_ZONE,
    SCROLL_SPEED,
    MOUSE_SENSITIVITY,
    MOUSE_ACCELERATION,
    MOUSE_STABILITY_ALPHA,
    MOUSE_DEAD_BAND,
    MOUSE_SCROLL_GESTURE,
)


class MouseController:
    def __init__(self):
        self._positions = deque(maxlen=max(1, SMOOTH_FACTOR))
        self._pinch_active = False
        self._fist_active = False
        self._thumbs_active = False
        self._drag_active = False
        self._prev_middle_y = None
        self._filtered_norm_pos = None
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0

    def _apply_dead_zone(self, value):
        low = DEAD_ZONE
        high = 1.0 - DEAD_ZONE
        if value <= low:
            return 0.0
        if value >= high:
            return 1.0
        return (value - low) / (high - low)

    def _smooth(self, x, y):
        self._positions.append((x, y))
        sx = sum(px for px, _ in self._positions) / len(self._positions)
        sy = sum(py for _, py in self._positions) / len(self._positions)
        return int(sx), int(sy)

    def _apply_sensitivity(self, value):
        centered = value - 0.5
        adjusted = 0.5 + centered * MOUSE_SENSITIVITY
        return max(0.0, min(1.0, adjusted))

    def update(self, landmarks, gesture, screen_w, screen_h):
        if landmarks is None or len(landmarks) < 21:
            self.reset()
            return

        idx_tip = landmarks[8]
        raw_nx = self._apply_sensitivity(self._apply_dead_zone(idx_tip.x))
        raw_ny = self._apply_sensitivity(self._apply_dead_zone(idx_tip.y))

        if self._filtered_norm_pos is None:
            nx, ny = raw_nx, raw_ny
        else:
            prev_nx, prev_ny = self._filtered_norm_pos
            if abs(raw_nx - prev_nx) < MOUSE_DEAD_BAND:
                raw_nx = prev_nx
            if abs(raw_ny - prev_ny) < MOUSE_DEAD_BAND:
                raw_ny = prev_ny
            nx = prev_nx + MOUSE_STABILITY_ALPHA * (raw_nx - prev_nx)
            ny = prev_ny + MOUSE_STABILITY_ALPHA * (raw_ny - prev_ny)

        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        self._filtered_norm_pos = (nx, ny)

        x = nx * (screen_w - 1)
        y = ny * (screen_h - 1)
        mx, my = self._smooth(x, y)
        pyautogui.moveTo(mx, my)

        if gesture == "PINCH":
            if not self._pinch_active:
                pyautogui.click(button='left')
                self._pinch_active = True
        elif gesture == "OPEN":
            self._pinch_active = False
        elif gesture != "PINCH":
            self._pinch_active = False

        if gesture == "FIST":
            if not self._fist_active:
                pyautogui.click(button='right')
                self._fist_active = True
        elif gesture != "FIST":
            self._fist_active = False

        if gesture == "THUMBS_UP":
            if not self._thumbs_active:
                pyautogui.doubleClick()
                self._thumbs_active = True
        elif gesture != "THUMBS_UP":
            self._thumbs_active = False

        if gesture == MOUSE_SCROLL_GESTURE:
            middle_y = landmarks[12].y
            if self._prev_middle_y is not None:
                delta = middle_y - self._prev_middle_y
                amount = int(-delta * screen_h * SCROLL_SPEED)
                if amount != 0:
                    pyautogui.scroll(amount)
            self._prev_middle_y = middle_y
        else:
            self._prev_middle_y = None

        if gesture == "PEACE" and MOUSE_SCROLL_GESTURE != "PEACE":
            if not self._drag_active:
                pyautogui.mouseDown(button='left')
                self._drag_active = True
        else:
            if self._drag_active:
                pyautogui.mouseUp(button='left')
                self._drag_active = False

    def reset(self):
        self._positions.clear()
        self._pinch_active = False
        self._fist_active = False
        self._thumbs_active = False
        self._prev_middle_y = None
        self._filtered_norm_pos = None
        if self._drag_active:
            pyautogui.mouseUp(button='left')
            self._drag_active = False
