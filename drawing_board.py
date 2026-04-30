# drawing_board.py
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2

from config import DRAWING_BRUSH_SIZE, DRAWING_COLORS, DRAWING_DRAG_PICK_RADIUS


Point = Tuple[int, int]
Color = Tuple[int, int, int]


@dataclass
class Stroke:
    points: List[Point]
    color: Color
    thickness: int


class DrawingBoard:
    def __init__(self):
        self.enabled = False
        self.strokes: List[Stroke] = []
        self._active_points: List[Point] = []
        self._color_index = 0
        self._drag_index: Optional[int] = None
        self._drag_last_cursor: Optional[Point] = None

    @property
    def current_color(self) -> Color:
        return DRAWING_COLORS[self._color_index]

    @property
    def current_color_name(self) -> str:
        names = ["CYAN", "GREEN", "AMBER", "CORAL", "VIOLET"]
        return names[self._color_index % len(names)]

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self._active_points = []
            self._drag_index = None
            self._drag_last_cursor = None

    def cycle_color(self):
        self._color_index = (self._color_index + 1) % len(DRAWING_COLORS)

    def clear(self):
        self.strokes.clear()
        self._active_points = []
        self._drag_index = None
        self._drag_last_cursor = None

    def _stroke_bounds(self, stroke: Stroke):
        xs = [pt[0] for pt in stroke.points]
        ys = [pt[1] for pt in stroke.points]
        return min(xs), min(ys), max(xs), max(ys)

    def _nearest_stroke_index(self, cursor: Point):
        cx, cy = cursor
        best_idx = None
        best_dist = float("inf")

        for idx, stroke in enumerate(self.strokes):
            x0, y0, x1, y1 = self._stroke_bounds(stroke)
            px = max(x0, min(cx, x1))
            py = max(y0, min(cy, y1))
            dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_idx = idx

        if best_idx is None or best_dist > DRAWING_DRAG_PICK_RADIUS:
            return None
        return best_idx

    def update(self, cursor: Optional[Point], dominant_pinch: bool, support_pinch: bool, dominant_gesture: str):
        if not self.enabled or cursor is None:
            self._active_points = []
            self._drag_index = None
            self._drag_last_cursor = None
            return "DRAW OFF"

        if support_pinch and self.strokes:
            if self._drag_index is None:
                self._drag_index = self._nearest_stroke_index(cursor)
                self._drag_last_cursor = cursor
            if self._drag_index is not None and self._drag_last_cursor is not None:
                dx = cursor[0] - self._drag_last_cursor[0]
                dy = cursor[1] - self._drag_last_cursor[1]
                if dx != 0 or dy != 0:
                    stroke = self.strokes[self._drag_index]
                    stroke.points = [(x + dx, y + dy) for (x, y) in stroke.points]
                self._drag_last_cursor = cursor
                return "DRAW DRAG STROKE"

        self._drag_index = None
        self._drag_last_cursor = None

        if dominant_pinch:
            self._active_points.append(cursor)
            if len(self._active_points) > 1:
                return "DRAW STROKE"
            return "DRAW READY"

        if len(self._active_points) > 1:
            self.strokes.append(
                Stroke(
                    points=list(self._active_points),
                    color=self.current_color,
                    thickness=DRAWING_BRUSH_SIZE,
                )
            )
        self._active_points = []

        if dominant_gesture == "POINT":
            return "DRAW AIM"
        return "DRAW IDLE"

    def render(self, frame):
        if not self.enabled:
            return frame

        overlay = frame.copy()
        for stroke in self.strokes:
            if len(stroke.points) < 2:
                continue
            for p0, p1 in zip(stroke.points[:-1], stroke.points[1:]):
                cv2.line(overlay, p0, p1, stroke.color, stroke.thickness, cv2.LINE_AA)

        if len(self._active_points) > 1:
            for p0, p1 in zip(self._active_points[:-1], self._active_points[1:]):
                cv2.line(overlay, p0, p1, self.current_color, DRAWING_BRUSH_SIZE, cv2.LINE_AA)

        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        return frame
