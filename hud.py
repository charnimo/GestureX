import cv2
from config import MODE_MOUSE, MODE_THEREMIN


def draw_hud(frame, mode, gesture, freq, volume, waveform):
    h, w = frame.shape[:2]

    panel_w = int(w * 0.36)
    panel_h = int(h * 0.18)
    panel_x = int(w * 0.02)
    panel_y = int(h * 0.03)

    overlay = frame.copy()
    cv2.rectangle(
        overlay,
        (panel_x, panel_y),
        (panel_x + panel_w, panel_y + panel_h),
        (20, 20, 20),
        -1,
    )
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    mode_color = (0, 255, 255) if mode == MODE_MOUSE else (0, 165, 255)
    cv2.putText(frame, f"MODE: {mode}", (panel_x + int(w * 0.01), panel_y + int(h * 0.055)),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, mode_color, 2, cv2.LINE_AA)
    cv2.putText(frame, f"GESTURE: {gesture}", (panel_x + int(w * 0.01), panel_y + int(h * 0.11)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    hint_x = int(w * 0.73)
    hint_y = int(h * 0.06)
    cv2.putText(frame, "[SPACE] toggle mode", (hint_x, hint_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    if mode == MODE_THEREMIN:
        bottom_h = int(h * 0.2)
        bottom_w = int(w * 0.42)
        bottom_x = int(w * 0.02)
        bottom_y = h - int(h * 0.03) - bottom_h

        overlay2 = frame.copy()
        cv2.rectangle(
            overlay2,
            (bottom_x, bottom_y),
            (bottom_x + bottom_w, bottom_y + bottom_h),
            (20, 20, 20),
            -1,
        )
        cv2.addWeighted(overlay2, 0.55, frame, 0.45, 0, frame)

        cv2.putText(frame, f"FREQ: {int(freq)} Hz", (bottom_x + int(w * 0.01), bottom_y + int(h * 0.06)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        bar_x = bottom_x + int(w * 0.01)
        bar_y = bottom_y + int(h * 0.1)
        bar_w = int(bottom_w * 0.85)
        bar_h = int(h * 0.03)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), 1)
        fill_w = int(bar_w * max(0.0, min(1.0, volume)))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 200, 255), -1)

        cv2.putText(frame, f"WAVE: {waveform}", (bottom_x + int(w * 0.01), bottom_y + int(h * 0.165)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "[W] next waveform", (hint_x, hint_y + int(h * 0.05)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    return frame
