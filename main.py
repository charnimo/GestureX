# main.py
import cv2
import keyboard
import pyautogui
import time

from config import *
from drawing_board import DrawingBoard
from gesture import classify_gesture
from hand_tracker import HandTracker
from hud import draw_hud
from mouse_control import MouseController
from theremin import Theremin


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    tracker = HandTracker()
    mouse_controller = MouseController()
    drawing_board = DrawingBoard()
    theremin = Theremin()

    screen_w, screen_h = pyautogui.size()
    mode = MODE_MOUSE
    running = True
    dominant_handedness = "Right"
    current_gesture = "UNKNOWN"
    support_gesture = "UNKNOWN"
    gesture_action_last_ms = {}
    last_frame_ts = time.perf_counter()
    smoothed_fps = float(TARGET_FPS)

    def toggle_mode():
        nonlocal mode
        mode = MODE_THEREMIN if mode == MODE_MOUSE else MODE_MOUSE
        if mode == MODE_THEREMIN:
            mouse_controller.reset()

    def next_waveform():
        if mode == MODE_THEREMIN:
            theremin.next_waveform()

    def next_scale():
        if mode == MODE_THEREMIN:
            theremin.next_scale()

    def next_key():
        if mode == MODE_THEREMIN:
            theremin.next_key()

    def request_exit():
        nonlocal running
        running = False

    def toggle_drawing_board():
        if mode == MODE_MOUSE:
            drawing_board.toggle()

    def _maybe_run_mouse_gesture_action(gesture_name):
        action = MOUSE_MODE_GESTURE_BINDINGS.get(gesture_name)
        if action is None:
            return

        now_ms = time.monotonic() * 1000.0
        last_ms = gesture_action_last_ms.get(action, 0.0)
        if (now_ms - last_ms) < GESTURE_ACTION_COOLDOWN_MS:
            return

        if action == "TOGGLE_DRAWING_BOARD":
            drawing_board.toggle()
            mouse_controller.status_text = "DRAW BOARD ON" if drawing_board.enabled else "DRAW BOARD OFF"
        elif action == "CYCLE_DRAWING_COLOR":
            drawing_board.cycle_color()
            mouse_controller.status_text = f"DRAW COLOR {drawing_board.current_color_name}"
        elif action == "CLEAR_DRAWING":
            drawing_board.clear()
            mouse_controller.status_text = "DRAW CLEAR"

        gesture_action_last_ms[action] = now_ms

    keyboard.add_hotkey(TOGGLE_KEY, toggle_mode)
    keyboard.add_hotkey("w", next_waveform)
    keyboard.add_hotkey("s", next_scale)
    keyboard.add_hotkey("k", next_key)
    keyboard.add_hotkey("d", toggle_drawing_board)
    keyboard.add_hotkey("q", request_exit)

    try:
        while running:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            hands = tracker.process(frame)
            by_hand = {hand.handedness: hand for hand in hands}

            left = by_hand.get("Left")
            right = by_hand.get("Right")
            dominant = by_hand.get(dominant_handedness)
            support = left if dominant_handedness == "Right" else right

            if dominant is not None:
                current_gesture = classify_gesture(dominant.landmark)
            else:
                current_gesture = "UNKNOWN"

            if support is not None:
                support_gesture = classify_gesture(support.landmark)
            else:
                support_gesture = "UNKNOWN"

            now_ts = time.perf_counter()
            dt = max(1e-5, now_ts - last_frame_ts)
            last_frame_ts = now_ts
            current_fps = 1.0 / dt
            smoothed_fps += 0.12 * (current_fps - smoothed_fps)
            fps_text = f"FPS: {smoothed_fps:.1f}"

            if mode == MODE_MOUSE:
                if dominant is not None:
                    _maybe_run_mouse_gesture_action(current_gesture)

                if dominant is not None:
                    mouse_controller.update(
                        dominant.landmark,
                        current_gesture,
                        screen_w,
                        screen_h,
                        support.landmark if support else None,
                        support_gesture,
                        app_draw_mode=drawing_board.enabled,
                    )

                    draw_status = drawing_board.update(
                        (mouse_controller.cursor_x, mouse_controller.cursor_y),
                        mouse_controller.dominant_pinch_active,
                        mouse_controller.support_pinch_active,
                        current_gesture,
                    )
                    if drawing_board.enabled:
                        mouse_controller.status_text = draw_status
                else:
                    mouse_controller.reset()
                    drawing_board.update(None, False, False, "UNKNOWN")
            else:
                theremin.update(
                    left.landmark if left else None,
                    right.landmark if right else None,
                    current_gesture,
                )

            tracker.draw_landmarks(frame, hands)
            if mode == MODE_MOUSE:
                drawing_board.render(frame)

            note_guide = theremin.get_note_trigger_guide()
            recent_notes = theremin.get_recent_notes()
            draw_hud(
                frame,
                mode,
                current_gesture,
                theremin.current_freq,
                theremin.current_volume,
                WAVEFORMS[theremin.current_waveform_index],
                theremin.current_note_name,
                theremin.current_scale_name,
                theremin.current_key_name,
                theremin.current_sustain,
                support_gesture,
                mouse_controller.status_text,
                drawing_board.enabled,
                drawing_board.current_color_name,
                note_guide,
                recent_notes,
                fps_text,
            )
            cv2.imshow("Gesture Control", frame)

            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                running = False
    finally:
        keyboard.unhook_all_hotkeys()
        tracker.close()
        theremin.stop()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
