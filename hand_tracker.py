# hand_tracker.py
from dataclasses import dataclass
from typing import List
import cv2
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2


@dataclass
class Landmark:
    x: float
    y: float
    z: float


@dataclass
class HandResult:
    landmark: List[Landmark]
    handedness: str


class HandTracker:
    def __init__(self):
        self._detect_width = 640
        self._detect_height = 360
        self._mp_hands = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_drawing_styles = mp.solutions.drawing_styles
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

    def process(self, frame) -> List[HandResult]:
        small_bgr = cv2.resize(frame, (self._detect_width, self._detect_height), interpolation=cv2.INTER_LINEAR)
        small_rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
        results = self._hands.process(small_rgb)

        hands_out: List[HandResult] = []
        if not results.multi_hand_landmarks or not results.multi_handedness:
            return hands_out

        for hand_lms, hand_info in zip(results.multi_hand_landmarks, results.multi_handedness):
            converted = []
            for lm in hand_lms.landmark:
                # MediaPipe already returns normalized coordinates (0..1)
                # relative to the processed frame dimensions.
                nx = min(max(lm.x, 0.0), 1.0)
                ny = min(max(lm.y, 0.0), 1.0)
                converted.append(Landmark(x=nx, y=ny, z=lm.z))

            handedness = hand_info.classification[0].label
            hands_out.append(HandResult(landmark=converted, handedness=handedness))

        return hands_out[:2]

    def draw_landmarks(self, frame, results: List[HandResult]):
        for hand in results:
            proto = landmark_pb2.NormalizedLandmarkList(
                landmark=[
                    landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z)
                    for lm in hand.landmark
                ]
            )
            self._mp_drawing.draw_landmarks(
                frame,
                proto,
                self._mp_hands.HAND_CONNECTIONS,
                self._mp_drawing_styles.get_default_hand_landmarks_style(),
                self._mp_drawing_styles.get_default_hand_connections_style(),
            )
        return frame

    def close(self):
        self._hands.close()
