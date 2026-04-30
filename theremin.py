# theremin.py
import numpy as np
import pygame
from collections import deque
from config import (
    SAMPLE_RATE,
    BUFFER_SIZE,
    VOLUME_SMOOTH,
    TIMBRE_SMOOTH,
    VOLUME_CURVE,
    VIBRATO_RATE,
    VIBRATO_DEPTH_MAX,
    OUTPUT_GAIN,
    WAVEFORMS,
    MUSICAL_KEYS,
    MUSICAL_SCALES,
    MUSIC_NOTE_RANGE,
    THEREMIN_MODE_GESTURE_BINDINGS,
    MUSIC_GUIDE_STEPS,
)


class Theremin:
    def __init__(self):
        pygame.mixer.pre_init(
            frequency=SAMPLE_RATE,
            size=-16,
            channels=1,
            buffer=BUFFER_SIZE,
        )
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=BUFFER_SIZE)

        self.current_freq = 440.0
        self.current_volume = 0.0
        self.current_waveform_index = 0
        self.current_brightness = 0.45
        self.current_key_index = 0
        self.current_scale_index = 0
        self.current_note_midi = 60
        self.current_note_name = "C4"
        self.current_key_name = MUSICAL_KEYS[self.current_key_index]
        self.current_scale_name = MUSICAL_SCALES[self.current_scale_index][0]
        self.current_sustain = False
        self._last_generated_freq = self.current_freq
        self._sample_cursor = 0
        self._note_history = deque(maxlen=10)
        init_state = pygame.mixer.get_init()
        self._mixer_channels = init_state[2] if init_state else 1
        self._gesture_latch = {
            "PINCH": False,
            "PEACE": False,
            "THUMBS_UP": False,
            "FIST": False,
            "ROCK": False,
            "THREE": False,
            "OK": False,
        }

        self._sound = None
        self._channel = None
        self._scale_notes = []
        self._rebuild_scale_notes()
        self.current_freq = self._midi_to_frequency(self.current_note_midi)
        self._regenerate_sound(force=True)

    @staticmethod
    def _midi_to_frequency(midi_note):
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    @staticmethod
    def _midi_to_name(midi_note):
        note_names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        octave = (midi_note // 12) - 1
        return f"{note_names[midi_note % 12]}{octave}"

    def _rebuild_scale_notes(self):
        scale_name, intervals = MUSICAL_SCALES[self.current_scale_index]
        root_semitone = MUSICAL_KEYS.index(MUSICAL_KEYS[self.current_key_index])
        low_midi, high_midi = MUSIC_NOTE_RANGE

        notes = []
        start_octave = (low_midi // 12) - 2
        end_octave = (high_midi // 12) + 2
        for octave in range(start_octave, end_octave + 1):
            base = root_semitone + 12 * octave
            for interval in intervals:
                midi_note = base + interval
                if low_midi <= midi_note <= high_midi:
                    notes.append(midi_note)

        notes = sorted(set(notes))
        if not notes:
            notes = [60]

        self._scale_notes = notes
        self.current_key_name = MUSICAL_KEYS[self.current_key_index]
        self.current_scale_name = scale_name

        if self.current_note_midi not in self._scale_notes:
            nearest = min(self._scale_notes, key=lambda midi_note: abs(midi_note - self.current_note_midi))
            self.current_note_midi = nearest
        self.current_note_name = self._midi_to_name(self.current_note_midi)
        self.current_freq = self._midi_to_frequency(self.current_note_midi)

    def _set_note_from_landmark(self, wrist_y):
        if not self._scale_notes:
            return

        clamped = min(max(wrist_y, 0.0), 1.0)
        target_index = int(round((1.0 - clamped) * (len(self._scale_notes) - 1)))
        target_index = max(0, min(len(self._scale_notes) - 1, target_index))
        target_midi = self._scale_notes[target_index]

        if target_midi != self.current_note_midi:
            self.current_note_midi = target_midi
            self.current_note_name = self._midi_to_name(target_midi)
            self._note_history.appendleft(self.current_note_name)
            self.current_freq = self._midi_to_frequency(target_midi)
            self._regenerate_sound(force=True)

    def _perform_action(self, action):
        if action == "TOGGLE_SUSTAIN":
            self.current_sustain = not self.current_sustain
        elif action == "NEXT_SCALE":
            self.next_scale()
        elif action == "NEXT_KEY":
            self.next_key()
        elif action == "NEXT_VOICE":
            self.next_waveform()

    def _handle_gesture_shortcuts(self, gesture):
        for key in self._gesture_latch:
            if key != gesture:
                self._gesture_latch[key] = False

        if gesture in THEREMIN_MODE_GESTURE_BINDINGS:
            action = THEREMIN_MODE_GESTURE_BINDINGS[gesture]
            latched = self._gesture_latch.get(gesture, False)
            if not latched:
                self._perform_action(action)
                self._gesture_latch[gesture] = True
            return

        if gesture == "PINCH":
            if not self._gesture_latch["PINCH"]:
                self.current_sustain = not self.current_sustain
                self._gesture_latch["PINCH"] = True
        else:
            self._gesture_latch["PINCH"] = False

        if gesture == "PEACE":
            if not self._gesture_latch["PEACE"]:
                self.next_scale()
                self._gesture_latch["PEACE"] = True
        else:
            self._gesture_latch["PEACE"] = False

        if gesture == "THUMBS_UP":
            if not self._gesture_latch["THUMBS_UP"]:
                self.next_key()
                self._gesture_latch["THUMBS_UP"] = True
        else:
            self._gesture_latch["THUMBS_UP"] = False

        if gesture == "FIST":
            if not self._gesture_latch["FIST"]:
                self.next_waveform()
                self._gesture_latch["FIST"] = True
        else:
            self._gesture_latch["FIST"] = False

    def get_recent_notes(self):
        if not self._note_history:
            return [self.current_note_name]
        return list(self._note_history)

    def get_note_trigger_guide(self, steps=MUSIC_GUIDE_STEPS):
        if not self._scale_notes:
            return []

        steps = max(3, int(steps))
        guide = []
        for slot in range(steps):
            slot_ratio = slot / max(1, (steps - 1))
            idx = int(round((1.0 - slot_ratio) * (len(self._scale_notes) - 1)))
            idx = max(0, min(len(self._scale_notes) - 1, idx))
            midi_note = self._scale_notes[idx]
            note_name = self._midi_to_name(midi_note)
            guide.append({"slot": slot, "ratio": slot_ratio, "note": note_name})
        return guide

    def _generate_wave(self, freq, waveform, duration_frames):
        t = (np.arange(duration_frames, dtype=np.float32) + self._sample_cursor) / SAMPLE_RATE
        freq = max(1.0, freq)
        phase = 2.0 * np.pi * freq * t
        voice = waveform.lower()

        def harmonic_sum(partials, inharmonicity=0.0):
            mix = np.zeros(duration_frames, dtype=np.float32)
            for partial, amp in partials:
                detune = 1.0 + inharmonicity * (partial ** 2)
                mix += amp * np.sin(2.0 * np.pi * freq * partial * detune * t)
            return mix

        rng = np.random.default_rng(self._sample_cursor % (2 ** 32))

        if voice == "piano":
            wave = harmonic_sum(
                [(1, 1.00), (2, 0.55), (3, 0.30), (4, 0.18), (5, 0.12), (6, 0.08), (7, 0.05), (8, 0.04)],
                inharmonicity=0.00018,
            )
            wave += 0.035 * np.exp(-t * 38.0) * np.sin(2.0 * np.pi * freq * 12.0 * t)
            attack, decay, sustain_level, release = 0.010, 0.18, 0.28, 0.20
        elif voice == "guitar":
            wave = harmonic_sum(
                [(1, 1.00), (2, 0.46), (3, 0.28), (4, 0.18), (5, 0.12), (6, 0.08), (7, 0.05)],
                inharmonicity=0.00008,
            )
            wave += 0.020 * np.exp(-t * 52.0) * rng.normal(0.0, 1.0, duration_frames).astype(np.float32)
            attack, decay, sustain_level, release = 0.006, 0.12, 0.18, 0.14
        elif voice == "violin":
            vibrato = 1.0 + VIBRATO_DEPTH_MAX * (0.75 + 0.25 * self.current_brightness) * np.sin(2.0 * np.pi * VIBRATO_RATE * t)
            wave = (
                np.sin(phase * vibrato)
                + 0.48 * np.sin(2.0 * phase * vibrato)
                + 0.22 * np.sin(3.0 * phase * vibrato)
                + 0.12 * np.sin(4.0 * phase * vibrato)
                + 0.07 * np.sin(5.0 * phase * vibrato)
            )
            wave += 0.015 * np.sin(2.0 * np.pi * (freq * 2.01) * t)
            attack, decay, sustain_level, release = 0.080, 0.16, 0.74, 0.18
        else:
            wave = (
                0.92 * np.sin(phase)
                + 0.10 * np.sin(2.0 * phase)
                + 0.04 * np.sin(3.0 * phase)
            )
            wave += 0.010 * np.exp(-t * 42.0) * rng.normal(0.0, 1.0, duration_frames).astype(np.float32)
            attack, decay, sustain_level, release = 0.025, 0.10, 0.82, 0.10

        brightness_mix = 0.25 + 0.75 * self.current_brightness
        wave = wave * brightness_mix + np.sin(phase) * (1.0 - brightness_mix)

        peak = np.max(np.abs(wave))
        if peak > 1e-6:
            wave = wave / peak
        attack_frames = max(8, int(duration_frames * attack))
        decay_frames = max(8, int(duration_frames * decay))
        release_frames = max(8, int(duration_frames * release))
        sustain_frames = max(0, duration_frames - attack_frames - decay_frames - release_frames)
        envelope = np.concatenate([
            np.linspace(0.0, 1.0, attack_frames, dtype=np.float32),
            np.linspace(1.0, sustain_level, decay_frames, dtype=np.float32),
            np.full(sustain_frames, sustain_level, dtype=np.float32),
            np.linspace(sustain_level, 0.0, release_frames, dtype=np.float32),
        ])
        if len(envelope) < duration_frames:
            envelope = np.pad(envelope, (0, duration_frames - len(envelope)), mode="constant")
        elif len(envelope) > duration_frames:
            envelope = envelope[:duration_frames]

        level = (self.current_volume ** VOLUME_CURVE) * OUTPUT_GAIN
        scaled = np.clip(wave * envelope * level, -1.0, 1.0)
        mono = (scaled * 32767).astype(np.int16)
        if self._mixer_channels == 1:
            return mono
        return np.repeat(mono[:, None], self._mixer_channels, axis=1)

    def _regenerate_sound(self, force=False):
        if not force and abs(self.current_freq - self._last_generated_freq) <= 1.0:
            return

        waveform = WAVEFORMS[self.current_waveform_index]
        duration_frames = int(SAMPLE_RATE * 1.25)
        samples = self._generate_wave(self.current_freq, waveform, duration_frames)
        self._sample_cursor += duration_frames
        self._sound = pygame.sndarray.make_sound(samples)

        if self._channel is not None and self._channel.get_busy():
            self._channel.stop()
        self._channel = self._sound.play(loops=-1)
        if self._channel is not None:
            self._channel.set_volume(self.current_volume)

        self._last_generated_freq = self.current_freq

    def update(self, left_hand_landmarks, right_hand_landmarks, gesture=None):
        if gesture is not None:
            self._handle_gesture_shortcuts(gesture)

        if left_hand_landmarks is not None and len(left_hand_landmarks) >= 1:
            wrist_y = min(max(left_hand_landmarks[0].y, 0.0), 1.0)
            if not self.current_sustain:
                self._set_note_from_landmark(wrist_y)

            index_x = min(max(left_hand_landmarks[8].x, 0.0), 1.0) if len(left_hand_landmarks) > 8 else 0.5
            target_brightness = 0.2 + 0.8 * index_x
            self.current_brightness += TIMBRE_SMOOTH * (target_brightness - self.current_brightness)

        target_volume = 0.0
        if right_hand_landmarks is not None and len(right_hand_landmarks) >= 1:
            wrist_y = min(max(right_hand_landmarks[0].y, 0.0), 1.0)
            target_volume = max(0.0, min(1.0, 1.0 - wrist_y))

        self.current_volume += VOLUME_SMOOTH * (target_volume - self.current_volume)
        self.current_volume = max(0.0, min(1.0, self.current_volume))

        self._regenerate_sound(force=False)
        if self._channel is not None:
            self._channel.set_volume(self.current_volume)

    def next_waveform(self):
        self.current_waveform_index = (self.current_waveform_index + 1) % len(WAVEFORMS)
        self._regenerate_sound(force=True)

    def next_scale(self):
        self.current_scale_index = (self.current_scale_index + 1) % len(MUSICAL_SCALES)
        self._rebuild_scale_notes()
        self._regenerate_sound(force=True)

    def next_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(MUSICAL_KEYS)
        self._rebuild_scale_notes()
        self._regenerate_sound(force=True)

    def stop(self):
        pygame.mixer.fadeout(200)
        pygame.mixer.quit()
