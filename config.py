CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 60

# Mouse
SMOOTH_FACTOR = 10          # higher = more smoothing (1-10)
CLICK_PINCH_THRESHOLD = 0.08 # normalized distance for pinch
SCROLL_SPEED = 10
DEAD_ZONE = 0.02           # fraction of screen edge to ignore
MOUSE_SENSITIVITY = 0.94   # <1 trims sensitivity for calmer control
MOUSE_ACCELERATION = 0.0   # keep cursor stable; range comes from sensitivity
MOUSE_STABILITY_ALPHA = 0.22  # lower = more stable cursor motion
MOUSE_DEAD_BAND = 0.058    # ignore tiny hand jitter in normalized space
MOUSE_SCROLL_GESTURE = "PEACE"
MOUSE_SLOW_ALPHA = 0.13    # smoothing when hand moves slowly
MOUSE_FAST_ALPHA = 0.46    # smoothing when hand moves quickly
MOUSE_FAST_DELTA = 0.040   # normalized delta considered fast movement
PINCH_DOWN_THRESHOLD = 0.040  # dominant pinch engage threshold
PINCH_UP_THRESHOLD = 0.062    # dominant pinch release threshold
DRAW_SLOW_ALPHA = 0.50     # less lag while drawing slowly
DRAW_FAST_ALPHA = 0.92     # high responsiveness while drawing
DRAW_DEAD_BAND = 0.002     # smaller dead band during pinch-draw
DRAW_RELATIVE_GAIN = 1.20  # boosts hand delta while drawing
DRAW_MAX_STEP_PX = 90      # cap per-frame draw movement to avoid spikes
MOUSE_RANGE_EASE = 0.015   # adaptive range update rate for full-screen reach
MOUSE_RANGE_MARGIN = 0.05  # initial hand-space margin for calibration
VOLUME_STEP_THRESHOLD = 0.08  # min normalized change before volume step
ZOOM_TRIGGER_DELTA = 0.03  # wrist travel needed to trigger zoom step
SUPPORT_CLICK_ENABLED = True
SUPPORT_PINCH_DOWN_THRESHOLD = 0.032
SUPPORT_PINCH_UP_THRESHOLD = 0.050
CLICK_DEBOUNCE_MS = 220
PINCH_ANCHOR_FRAMES = 6
DRAG_HOLD_MS = 120
CURSOR_MIN_MOVE_PX = 2
GESTURE_ACTION_COOLDOWN_MS = 350

# Drawing board
DRAWING_BOARD_DEFAULT_ENABLED = False
DRAWING_BRUSH_SIZE = 4
DRAWING_DRAG_PICK_RADIUS = 45
DRAWING_COLORS = [
    (0, 245, 255),
    (70, 220, 90),
    (255, 190, 40),
    (255, 90, 70),
    (185, 120, 255),
]

# Custom gesture bindings
MOUSE_MODE_GESTURE_BINDINGS = {
    "ROCK": "TOGGLE_DRAWING_BOARD",
    "THREE": "CYCLE_DRAWING_COLOR",
    "OK": "CLEAR_DRAWING",
}
THEREMIN_MODE_GESTURE_BINDINGS = {
    "PINCH": "TOGGLE_SUSTAIN",
    "ROCK": "NEXT_VOICE",
    "THREE": "NEXT_SCALE",
    "THUMBS_UP": "NEXT_KEY",
}

# Theremin
MIN_FREQ = 110.0           # Hz, A2
MAX_FREQ = 1760.0          # Hz, A6
SAMPLE_RATE = 44100
BUFFER_SIZE = 512
VOLUME_SMOOTH = 0.15       # lerp factor for volume changes
PITCH_SMOOTH = 0.08        # lerp factor for pitch changes
TIMBRE_SMOOTH = 0.12       # lerp factor for brightness changes
VOLUME_CURVE = 0.7         # <1 gives more loudness at mid hand height
VIBRATO_RATE = 5.5         # Hz
VIBRATO_DEPTH_MAX = 0.018  # ~1.8% pitch modulation at max depth
OUTPUT_GAIN = 0.8          # global theremin loudness headroom
WAVEFORMS = ["Piano", "Guitar", "Violin", "Flute"]
MUSICAL_KEYS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
MUSICAL_SCALES = [
    ("Major", [0, 2, 4, 5, 7, 9, 11]),
    ("Natural Minor", [0, 2, 3, 5, 7, 8, 10]),
    ("Pentatonic Major", [0, 2, 4, 7, 9]),
    ("Pentatonic Minor", [0, 3, 5, 7, 10]),
    ("Blues", [0, 3, 5, 6, 7, 10]),
    ("Dorian", [0, 2, 3, 5, 7, 9, 10]),
    ("Mixolydian", [0, 2, 4, 5, 7, 9, 10]),
    ("Harmonic Minor", [0, 2, 3, 5, 7, 8, 11]),
]
MUSIC_NOTE_RANGE = (48, 84)   # C3 to C6
MUSIC_GUIDE_STEPS = 9

# Modes
MODE_MOUSE = "MOUSE"
MODE_THEREMIN = "THEREMIN"
TOGGLE_KEY = "space"
