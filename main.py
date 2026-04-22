import cv2
import keyboard
import pyautogui

from config import *
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
    theremin = Theremin()

    screen_w, screen_h = pyautogui.size()
    mode = MODE_MOUSE
    running = True
    dominant_handedness = "Right"
    current_gesture = "UNKNOWN"

    def toggle_mode():
        nonlocal mode
        mode = MODE_THEREMIN if mode == MODE_MOUSE else MODE_MOUSE
        if mode == MODE_THEREMIN:
            mouse_controller.reset()

    def next_waveform():
        if mode == MODE_THEREMIN:
            theremin.next_waveform()

    def request_exit():
        nonlocal running
        running = False

    keyboard.add_hotkey(TOGGLE_KEY, toggle_mode)
    keyboard.add_hotkey("w", next_waveform)
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

            if dominant is not None:
                current_gesture = classify_gesture(dominant.landmark)
            else:
                current_gesture = "UNKNOWN"

            if mode == MODE_MOUSE:
                if dominant is not None:
                    mouse_controller.update(dominant.landmark, current_gesture, screen_w, screen_h)
                else:
                    mouse_controller.reset()
            else:
                theremin.update(
                    left.landmark if left else None,
                    right.landmark if right else None,
                )

            tracker.draw_landmarks(frame, hands)
            draw_hud(
                frame,
                mode,
                current_gesture,
                theremin.current_freq,
                theremin.current_volume,
                WAVEFORMS[theremin.current_waveform_index],
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
