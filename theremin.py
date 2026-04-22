import numpy as np
import pygame
from config import (
    MIN_FREQ,
    MAX_FREQ,
    SAMPLE_RATE,
    BUFFER_SIZE,
    VOLUME_SMOOTH,
    PITCH_SMOOTH,
    TIMBRE_SMOOTH,
    VOLUME_CURVE,
    VIBRATO_RATE,
    VIBRATO_DEPTH_MAX,
    OUTPUT_GAIN,
    WAVEFORMS,
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
        self._last_generated_freq = self.current_freq
        self._sample_cursor = 0
        init_state = pygame.mixer.get_init()
        self._mixer_channels = init_state[2] if init_state else 1

        self._sound = None
        self._channel = None
        self._regenerate_sound(force=True)

    def _generate_wave(self, freq, waveform, duration_frames):
        t = (np.arange(duration_frames, dtype=np.float32) + self._sample_cursor) / SAMPLE_RATE
        vibrato = 1.0 + VIBRATO_DEPTH_MAX * self.current_brightness * np.sin(2.0 * np.pi * VIBRATO_RATE * t)
        mod_freq = max(1.0, freq) * vibrato
        phase = 2.0 * np.pi * mod_freq * t

        if waveform == "sine":
            base = np.sin(phase)
            harmonic = 0.30 * np.sin(2.0 * phase) + 0.12 * np.sin(3.0 * phase)
            wave = (1.0 - self.current_brightness) * base + self.current_brightness * (base + harmonic)
        elif waveform == "square":
            wave = (
                np.sin(phase)
                + 0.33 * np.sin(3.0 * phase)
                + 0.20 * np.sin(5.0 * phase)
                + 0.14 * np.sin(7.0 * phase)
            )
        elif waveform == "sawtooth":
            wave = (
                np.sin(phase)
                + 0.50 * np.sin(2.0 * phase)
                + 0.33 * np.sin(3.0 * phase)
                + 0.25 * np.sin(4.0 * phase)
                + 0.20 * np.sin(5.0 * phase)
            )
        else:
            wave = (
                np.sin(phase)
                - (1.0 / 9.0) * np.sin(3.0 * phase)
                + (1.0 / 25.0) * np.sin(5.0 * phase)
                - (1.0 / 49.0) * np.sin(7.0 * phase)
            )

        peak = np.max(np.abs(wave))
        if peak > 1e-6:
            wave = wave / peak

        # Short edge fade reduces loop-boundary clicks when buffers restart.
        edge = max(8, min(duration_frames // 12, 128))
        envelope = np.ones(duration_frames, dtype=np.float32)
        envelope[:edge] = np.linspace(0.0, 1.0, edge, dtype=np.float32)
        envelope[-edge:] = np.linspace(1.0, 0.0, edge, dtype=np.float32)

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
        duration_frames = int(SAMPLE_RATE * 0.18)
        samples = self._generate_wave(self.current_freq, waveform, duration_frames)
        self._sample_cursor += duration_frames
        self._sound = pygame.sndarray.make_sound(samples)

        if self._channel is not None and self._channel.get_busy():
            self._channel.stop()
        self._channel = self._sound.play(loops=-1)
        if self._channel is not None:
            self._channel.set_volume(self.current_volume)

        self._last_generated_freq = self.current_freq

    def update(self, left_hand_landmarks, right_hand_landmarks):
        if left_hand_landmarks is not None and len(left_hand_landmarks) >= 1:
            wrist_y = min(max(left_hand_landmarks[0].y, 0.0), 1.0)
            target_freq = MIN_FREQ * (MAX_FREQ / MIN_FREQ) ** (1.0 - wrist_y)
            self.current_freq += PITCH_SMOOTH * (target_freq - self.current_freq)

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

    def stop(self):
        pygame.mixer.fadeout(200)
        pygame.mixer.quit()
