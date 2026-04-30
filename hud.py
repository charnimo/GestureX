# hud.py
import cv2
from config import MODE_MOUSE, MODE_THEREMIN


def _frosted_panel(frame, x, y, panel_w, panel_h, alpha=0.45, color=(24, 26, 28)):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + panel_w, y + panel_h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)


def _draw_common_header(frame, mode, gesture, support_gesture, mouse_status, fps_text):
    h, w = frame.shape[:2]
    x, y = int(w * 0.02), int(h * 0.03)
    panel_w, panel_h = int(w * 0.40), int(h * 0.24)
    _frosted_panel(frame, x, y, panel_w, panel_h, alpha=0.55)

    mode_color = (86, 220, 255) if mode == MODE_MOUSE else (82, 190, 255)
    cv2.putText(frame, "GESTURE STUDIO", (x + 14, y + 28), cv2.FONT_HERSHEY_DUPLEX, 0.7, (235, 235, 235), 1, cv2.LINE_AA)
    cv2.putText(frame, f"MODE: {mode}", (x + 14, y + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.72, mode_color, 2, cv2.LINE_AA)
    cv2.putText(frame, f"GESTURE: {gesture}", (x + 14, y + 86), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (240, 240, 240), 1, cv2.LINE_AA)
    cv2.putText(frame, f"SUPPORT: {support_gesture}", (x + 14, y + 112), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (210, 230, 250), 1, cv2.LINE_AA)
    cv2.putText(frame, f"ACTION: {mouse_status}", (x + 14, y + 138), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (200, 245, 205), 1, cv2.LINE_AA)
    cv2.putText(frame, fps_text, (x + 14, y + 164), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 220, 220), 1, cv2.LINE_AA)


def _draw_mouse_legend(frame, drawing_enabled, drawing_color_name):
    h, w = frame.shape[:2]
    x, y = int(w * 0.53), int(h * 0.03)
    panel_w, panel_h = int(w * 0.45), int(h * 0.24)
    _frosted_panel(frame, x, y, panel_w, panel_h, alpha=0.50)

    cv2.putText(frame, "MOUSE / DRAW CONTROLS", (x + 14, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "support PINCH: click    support THUMBS_UP: volume", (x + 14, y + 62), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (240, 240, 240), 1, cv2.LINE_AA)
    cv2.putText(frame, "support PEACE: zoom     PEACE: scroll", (x + 14, y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (240, 240, 240), 1, cv2.LINE_AA)
    cv2.putText(frame, "ROCK: draw board on/off  THREE: cycle color", (x + 14, y + 108), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (240, 240, 240), 1, cv2.LINE_AA)
    cv2.putText(frame, "OK: clear drawing        support PINCH + draw: drag stroke", (x + 14, y + 131), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (240, 240, 240), 1, cv2.LINE_AA)
    cv2.putText(frame, f"DRAW BOARD: {'ON' if drawing_enabled else 'OFF'}  COLOR: {drawing_color_name}", (x + 14, y + 162), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (255, 215, 140), 1, cv2.LINE_AA)


def _draw_theremin_panel(frame, freq, volume, waveform, note_name, scale_name, key_name, sustain, note_guide, recent_notes):
    h, w = frame.shape[:2]

    left_x = int(w * 0.02)
    left_y = h - int(h * 0.30)
    left_w = int(w * 0.44)
    left_h = int(h * 0.27)
    _frosted_panel(frame, left_x, left_y, left_w, left_h, alpha=0.58)

    cv2.putText(frame, "LIVE INSTRUMENT", (left_x + 14, left_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"NOTE: {note_name}", (left_x + 14, left_y + 64), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (100, 230, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"KEY: {key_name}   SCALE: {scale_name}", (left_x + 14, left_y + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (225, 225, 225), 1, cv2.LINE_AA)
    cv2.putText(frame, f"VOICE: {waveform}   HOLD: {'ON' if sustain else 'OFF'}", (left_x + 14, left_y + 116), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (225, 225, 225), 1, cv2.LINE_AA)
    cv2.putText(frame, f"FREQ: {int(freq)} Hz", (left_x + 14, left_y + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (225, 225, 225), 1, cv2.LINE_AA)

    bar_x = left_x + 14
    bar_y = left_y + 156
    bar_w = left_w - 28
    bar_h = 18
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (85, 85, 85), 1)
    fill_w = int(bar_w * max(0.0, min(1.0, volume)))
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (90, 214, 255), -1)
    cv2.putText(frame, "Volume by right wrist height", (bar_x, bar_y + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.47, (220, 220, 220), 1, cv2.LINE_AA)

    recent = "  ".join(recent_notes[:6]) if recent_notes else note_name
    cv2.putText(frame, f"Recent notes: {recent}", (bar_x, bar_y + 62), cv2.FONT_HERSHEY_SIMPLEX, 0.47, (220, 220, 220), 1, cv2.LINE_AA)

    right_x = int(w * 0.50)
    right_y = h - int(h * 0.42)
    right_w = int(w * 0.48)
    right_h = int(h * 0.39)
    _frosted_panel(frame, right_x, right_y, right_w, right_h, alpha=0.56)
    cv2.putText(frame, "NOTE TRIGGER GUIDE (LEFT WRIST HEIGHT)", (right_x + 14, right_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Raise hand = higher notes", (right_x + 14, right_y + 56), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)

    if note_guide:
        ladder_top = right_y + 75
        ladder_bottom = right_y + right_h - 24
        ladder_x = right_x + 26
        cv2.line(frame, (ladder_x, ladder_top), (ladder_x, ladder_bottom), (170, 170, 170), 2)

        for item in note_guide:
            ratio = item["ratio"]
            note = item["note"]
            y = int(ladder_top + ratio * (ladder_bottom - ladder_top))
            active = note == note_name
            color = (100, 230, 255) if active else (220, 220, 220)
            radius = 7 if active else 5
            cv2.circle(frame, (ladder_x, y), radius, color, -1)
            cv2.putText(frame, note, (ladder_x + 16, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.50, color, 1, cv2.LINE_AA)

    cv2.putText(frame, "[W] next voice  [S] next scale  [K] next key", (right_x + 14, right_y + right_h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (240, 240, 240), 1, cv2.LINE_AA)


def draw_hud(
    frame,
    mode,
    gesture,
    freq,
    volume,
    waveform,
    note_name=None,
    scale_name=None,
    key_name=None,
    sustain=False,
    support_gesture="UNKNOWN",
    mouse_status="IDLE",
    drawing_enabled=False,
    drawing_color_name="CYAN",
    note_guide=None,
    recent_notes=None,
    fps_text="",
):
    _draw_common_header(frame, mode, gesture, support_gesture, mouse_status, fps_text)

    if mode == MODE_MOUSE:
        _draw_mouse_legend(frame, drawing_enabled, drawing_color_name)

    if mode == MODE_THEREMIN and note_name and scale_name and key_name:
        _draw_theremin_panel(
            frame,
            freq,
            volume,
            waveform,
            note_name,
            scale_name,
            key_name,
            sustain,
            note_guide or [],
            recent_notes or [],
        )

    return frame

