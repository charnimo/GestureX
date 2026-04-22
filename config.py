CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
TARGET_FPS = 60

# Mouse
SMOOTH_FACTOR = 3          # higher = more smoothing (1–10)
CLICK_PINCH_THRESHOLD = 0.04   # normalized distance for pinch
SCROLL_SPEED = 20
DEAD_ZONE = 0.02           # fraction of screen edge to ignore
MOUSE_SENSITIVITY = 1.45   # >1 expands movement around the center
MOUSE_ACCELERATION = 0.0   # keep cursor stable; range comes from sensitivity
MOUSE_STABILITY_ALPHA = 0.22  # lower = more stable cursor motion
MOUSE_DEAD_BAND = 0.006    # ignore tiny hand jitter in normalized space
MOUSE_SCROLL_GESTURE = "PEACE"

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
WAVEFORMS = ["sine", "square", "sawtooth", "triangle"]

# Modes
MODE_MOUSE = "MOUSE"
MODE_THEREMIN = "THEREMIN"
TOGGLE_KEY = "space"
