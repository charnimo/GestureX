# mouse_control.py
import math
import time
import pyautogui
from config import (
    DEAD_ZONE,
    SCROLL_SPEED,
    MOUSE_SENSITIVITY,
    MOUSE_DEAD_BAND,
    MOUSE_SCROLL_GESTURE,
    MOUSE_SLOW_ALPHA,
    MOUSE_FAST_ALPHA,
    MOUSE_FAST_DELTA,
    PINCH_DOWN_THRESHOLD,
    PINCH_UP_THRESHOLD,
    DRAW_SLOW_ALPHA,
    DRAW_FAST_ALPHA,
    DRAW_DEAD_BAND,
    DRAW_RELATIVE_GAIN,
    DRAW_MAX_STEP_PX,
    MOUSE_RANGE_EASE,
    MOUSE_RANGE_MARGIN,
    VOLUME_STEP_THRESHOLD,
    ZOOM_TRIGGER_DELTA,
    SUPPORT_CLICK_ENABLED,
    SUPPORT_PINCH_DOWN_THRESHOLD,
    SUPPORT_PINCH_UP_THRESHOLD,
    CLICK_DEBOUNCE_MS,
    PINCH_ANCHOR_FRAMES,
    DRAG_HOLD_MS,
    CURSOR_MIN_MOVE_PX,
)


class MouseController:
    def __init__(self):
        self._pinch_active = False
        self._dominant_pinch_state = False
        self._support_pinch_state = False
        self._fist_active = False
        self._thumbs_active = False
        self._drag_active = False
        self._drag_candidate_since_ms = None
        self._prev_middle_y = None
        self._filtered_norm_pos = None
        self._prev_cursor_norm = None
        self._draw_residual_x = 0.0
        self._draw_residual_y = 0.0
        self._range_min_x = None
        self._range_max_x = None
        self._range_min_y = None
        self._range_max_y = None
        self._zoom_accum = 0.0
        self._prev_zoom_y = None
        self._last_volume_level = None
        self._last_click_ms = 0.0
        self._pinch_anchor_norm = None
        self._pinch_anchor_frames_left = 0
        self.cursor_x = None
        self.cursor_y = None
        self.support_pinch_active = False
        self.dominant_pinch_active = False
        self.status_text = "IDLE"

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        if hasattr(pyautogui, "MINIMUM_DURATION"):
            pyautogui.MINIMUM_DURATION = 0
        if hasattr(pyautogui, "MINIMUM_SLEEP"):
            pyautogui.MINIMUM_SLEEP = 0

    def _apply_dead_zone(self, value):
        low = DEAD_ZONE
        high = 1.0 - DEAD_ZONE
        if value <= low:
            return 0.0
        if value >= high:
            return 1.0
        return (value - low) / (high - low)

    def _apply_sensitivity(self, value):
        centered = value - 0.5
        adjusted = 0.5 + centered * MOUSE_SENSITIVITY
        return max(0.0, min(1.0, adjusted))

    @staticmethod
    def _pinch_distance(landmarks):
        return math.dist(
            (landmarks[4].x, landmarks[4].y, landmarks[4].z),
            (landmarks[8].x, landmarks[8].y, landmarks[8].z),
        )

    def _pinched_with_hysteresis(self, landmarks, current_state, down_threshold, up_threshold):
        if landmarks is None or len(landmarks) < 9:
            return False
        dist = self._pinch_distance(landmarks)
        if current_state:
            return dist < up_threshold
        return dist < down_threshold

    def _adaptive_normalize(self, value, low, high):
        span = max(0.12, high - low)
        norm = (value - low) / span
        return max(0.0, min(1.0, norm))

    def _update_adaptive_range(self, x, y):
        margin = MOUSE_RANGE_MARGIN
        ease = MOUSE_RANGE_EASE

        if self._range_min_x is None:
            self._range_min_x = max(0.0, x - margin)
            self._range_max_x = min(1.0, x + margin)
            self._range_min_y = max(0.0, y - margin)
            self._range_max_y = min(1.0, y + margin)
            return

        if x < self._range_min_x:
            self._range_min_x = x
        else:
            self._range_min_x += ease * (x - self._range_min_x)

        if x > self._range_max_x:
            self._range_max_x = x
        else:
            self._range_max_x += ease * (x - self._range_max_x)

        if y < self._range_min_y:
            self._range_min_y = y
        else:
            self._range_min_y += ease * (y - self._range_min_y)

        if y > self._range_max_y:
            self._range_max_y = y
        else:
            self._range_max_y += ease * (y - self._range_max_y)

        self._range_min_x = max(0.0, min(self._range_min_x, 1.0 - margin))
        self._range_max_x = min(1.0, max(self._range_max_x, margin))
        self._range_min_y = max(0.0, min(self._range_min_y, 1.0 - margin))
        self._range_max_y = min(1.0, max(self._range_max_y, margin))

    def _update_system_volume(self, landmarks):
        if landmarks is None or len(landmarks) < 1:
            self._last_volume_level = None
            return

        level = max(0.0, min(1.0, 1.0 - landmarks[0].y))
        if self._last_volume_level is None:
            self._last_volume_level = level
            return

        delta = level - self._last_volume_level
        if abs(delta) < VOLUME_STEP_THRESHOLD:
            return

        steps = max(1, min(4, int(abs(delta) / VOLUME_STEP_THRESHOLD)))
        key = "volumeup" if delta > 0 else "volumedown"
        for _ in range(steps):
            pyautogui.press(key)
        self._last_volume_level = level
        self.status_text = f"VOLUME {int(level * 100)}%"

    def _handle_zoom(self, landmarks):
        if landmarks is None or len(landmarks) < 1:
            self._prev_zoom_y = None
            self._zoom_accum = 0.0
            return

        zoom_y = landmarks[0].y
        if self._prev_zoom_y is None:
            self._prev_zoom_y = zoom_y
            return

        dy = zoom_y - self._prev_zoom_y
        self._prev_zoom_y = zoom_y
        self._zoom_accum += dy

        if self._zoom_accum <= -ZOOM_TRIGGER_DELTA:
            pyautogui.hotkey("ctrl", "+")
            self._zoom_accum = 0.0
            self.status_text = "ZOOM IN"
        elif self._zoom_accum >= ZOOM_TRIGGER_DELTA:
            pyautogui.hotkey("ctrl", "-")
            self._zoom_accum = 0.0
            self.status_text = "ZOOM OUT"

    def _maybe_support_click(self, secondary_landmarks, now_ms):
        if not SUPPORT_CLICK_ENABLED:
            self._support_pinch_state = False
            return

        prev_state = self._support_pinch_state
        self._support_pinch_state = self._pinched_with_hysteresis(
            secondary_landmarks,
            self._support_pinch_state,
            SUPPORT_PINCH_DOWN_THRESHOLD,
            SUPPORT_PINCH_UP_THRESHOLD,
        )

        if self._support_pinch_state and not prev_state:
            if (now_ms - self._last_click_ms) >= CLICK_DEBOUNCE_MS:
                pyautogui.click(button="left")
                self._last_click_ms = now_ms
                self.status_text = "CLICK"

    def update(
        self,
        landmarks,
        gesture,
        screen_w,
        screen_h,
        secondary_landmarks=None,
        secondary_gesture="UNKNOWN",
        app_draw_mode=False,
    ):
        if landmarks is None or len(landmarks) < 21:
            self.reset()
            return

        now_ms = time.monotonic() * 1000.0
        self.status_text = "MOVE"

        self.support_pinch_active = self._pinched_with_hysteresis(
            secondary_landmarks,
            self.support_pinch_active,
            SUPPORT_PINCH_DOWN_THRESHOLD,
            SUPPORT_PINCH_UP_THRESHOLD,
        )
        self._support_pinch_state = self.support_pinch_active

        if not app_draw_mode:
            self._maybe_support_click(secondary_landmarks, now_ms)

        if (not app_draw_mode) and secondary_gesture == "THUMBS_UP":
            self._update_system_volume(secondary_landmarks)
        else:
            self._last_volume_level = None

        if (not app_draw_mode) and secondary_gesture == "PEACE":
            self._handle_zoom(secondary_landmarks)
        else:
            self._prev_zoom_y = None
            self._zoom_accum = 0.0

        prev_dominant_state = self._dominant_pinch_state
        self._dominant_pinch_state = self._pinched_with_hysteresis(
            landmarks,
            self._dominant_pinch_state,
            PINCH_DOWN_THRESHOLD,
            PINCH_UP_THRESHOLD,
        )
        self.dominant_pinch_active = self._dominant_pinch_state

        if self._dominant_pinch_state and not prev_dominant_state:
            self._drag_candidate_since_ms = now_ms
            self._pinch_anchor_frames_left = max(0, int(PINCH_ANCHOR_FRAMES))
            self._pinch_anchor_norm = self._prev_cursor_norm

        if not self._dominant_pinch_state:
            self._drag_candidate_since_ms = None
            self._pinch_anchor_frames_left = 0
            self._pinch_anchor_norm = None

        if self._dominant_pinch_state:
            raw_x = (landmarks[8].x + landmarks[4].x) * 0.5
            raw_y = (landmarks[8].y + landmarks[4].y) * 0.5
        else:
            raw_x = landmarks[8].x
            raw_y = landmarks[8].y

        self._update_adaptive_range(raw_x, raw_y)

        norm_x = self._adaptive_normalize(raw_x, self._range_min_x, self._range_max_x)
        norm_y = self._adaptive_normalize(raw_y, self._range_min_y, self._range_max_y)

        raw_nx = self._apply_sensitivity(self._apply_dead_zone(norm_x))
        raw_ny = self._apply_sensitivity(self._apply_dead_zone(norm_y))

        if self._filtered_norm_pos is None:
            nx, ny = raw_nx, raw_ny
        else:
            prev_nx, prev_ny = self._filtered_norm_pos
            dx = raw_nx - prev_nx
            dy = raw_ny - prev_ny
            speed = max(abs(dx), abs(dy))

            dead_band = DRAW_DEAD_BAND if self._dominant_pinch_state else MOUSE_DEAD_BAND
            if abs(dx) < dead_band:
                raw_nx = prev_nx
            if abs(dy) < dead_band:
                raw_ny = prev_ny

            blend = min(1.0, speed / max(MOUSE_FAST_DELTA, 1e-6))
            if self._dominant_pinch_state:
                alpha = DRAW_SLOW_ALPHA + (DRAW_FAST_ALPHA - DRAW_SLOW_ALPHA) * blend
            else:
                alpha = MOUSE_SLOW_ALPHA + (MOUSE_FAST_ALPHA - MOUSE_SLOW_ALPHA) * blend
            nx = prev_nx + alpha * (raw_nx - prev_nx)
            ny = prev_ny + alpha * (raw_ny - prev_ny)

        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        # Freeze briefly at pinch start to prevent click/drag target shift.
        if self._dominant_pinch_state and self._pinch_anchor_frames_left > 0 and self._pinch_anchor_norm is not None:
            nx, ny = self._pinch_anchor_norm
            self._pinch_anchor_frames_left -= 1
            self.status_text = "PINCH ANCHOR"

        self._filtered_norm_pos = (nx, ny)

        x = nx * (screen_w - 1)
        y = ny * (screen_h - 1)
        self.cursor_x = int(x)
        self.cursor_y = int(y)

        if self._dominant_pinch_state and self._pinch_active and self._prev_cursor_norm is not None:
            prev_cx, prev_cy = self._prev_cursor_norm
            dx_px = (nx - prev_cx) * (screen_w - 1) * DRAW_RELATIVE_GAIN + self._draw_residual_x
            dy_px = (ny - prev_cy) * (screen_h - 1) * DRAW_RELATIVE_GAIN + self._draw_residual_y

            max_step = max(1, int(DRAW_MAX_STEP_PX))
            dx_px = max(-max_step, min(max_step, dx_px))
            dy_px = max(-max_step, min(max_step, dy_px))

            step_x = int(round(dx_px))
            step_y = int(round(dy_px))
            self._draw_residual_x = dx_px - step_x
            self._draw_residual_y = dy_px - step_y

            if step_x != 0 or step_y != 0:
                pyautogui.moveRel(step_x, step_y)
            self.status_text = "AIR DRAW / DRAG"
        else:
            if self._prev_cursor_norm is not None:
                prev_cx, prev_cy = self._prev_cursor_norm
                dx_px = abs((nx - prev_cx) * (screen_w - 1))
                dy_px = abs((ny - prev_cy) * (screen_h - 1))
            else:
                dx_px, dy_px = CURSOR_MIN_MOVE_PX, CURSOR_MIN_MOVE_PX

            if dx_px >= CURSOR_MIN_MOVE_PX or dy_px >= CURSOR_MIN_MOVE_PX:
                pyautogui.moveTo(int(x), int(y))
            self._draw_residual_x = 0.0
            self._draw_residual_y = 0.0

        self._prev_cursor_norm = (nx, ny)

        if (not app_draw_mode) and self._dominant_pinch_state:
            if not self._pinch_active:
                if self._drag_candidate_since_ms is None:
                    self._drag_candidate_since_ms = now_ms
                elif (now_ms - self._drag_candidate_since_ms) >= DRAG_HOLD_MS:
                    pyautogui.mouseDown(button="left")
                    self._pinch_active = True
                    self.status_text = "HOLD DRAG"
        else:
            if self._pinch_active:
                pyautogui.mouseUp(button="left")
            self._pinch_active = False

        if (not app_draw_mode) and gesture == "FIST":
            if not self._fist_active:
                pyautogui.click(button="right")
                self._fist_active = True
                self.status_text = "RIGHT CLICK"
        else:
            self._fist_active = False

        if (not app_draw_mode) and gesture == "THUMBS_UP":
            if not self._thumbs_active:
                pyautogui.doubleClick()
                self._thumbs_active = True
                self.status_text = "DOUBLE CLICK"
        else:
            self._thumbs_active = False

        if (not app_draw_mode) and gesture == MOUSE_SCROLL_GESTURE:
            middle_y = landmarks[12].y
            if self._prev_middle_y is not None:
                delta = middle_y - self._prev_middle_y
                amount = int(-delta * screen_h * SCROLL_SPEED)
                if amount != 0:
                    pyautogui.scroll(amount)
                    self.status_text = "SCROLL"
            self._prev_middle_y = middle_y
        else:
            self._prev_middle_y = None

        if (not app_draw_mode) and gesture == "PEACE" and MOUSE_SCROLL_GESTURE != "PEACE":
            if not self._drag_active:
                pyautogui.mouseDown(button="left")
                self._drag_active = True
                self.status_text = "HOLD DRAG"
        else:
            if self._drag_active:
                pyautogui.mouseUp(button="left")
                self._drag_active = False

    def reset(self):
        if self._pinch_active:
            pyautogui.mouseUp(button="left")
        self._pinch_active = False
        self._dominant_pinch_state = False
        self._support_pinch_state = False
        self._fist_active = False
        self._thumbs_active = False
        self._prev_middle_y = None
        self._filtered_norm_pos = None
        self._prev_cursor_norm = None
        self._draw_residual_x = 0.0
        self._draw_residual_y = 0.0
        self._zoom_accum = 0.0
        self._prev_zoom_y = None
        self._last_volume_level = None
        self._drag_candidate_since_ms = None
        self._pinch_anchor_norm = None
        self._pinch_anchor_frames_left = 0
        self.cursor_x = None
        self.cursor_y = None
        self.support_pinch_active = False
        self.dominant_pinch_active = False
        self.status_text = "IDLE"
        if self._drag_active:
            pyautogui.mouseUp(button="left")
            self._drag_active = False
