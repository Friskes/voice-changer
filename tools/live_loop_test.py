"""Живой тест всего аудиотракта без человека: речь из файла идёт во второй кабель (VC_VIRTUAL_MIC) как в микрофон.

Движок отдаёт её в основной кабель при включённом мониторе с нулевой громкостью — ровно боевая схема.
Запуск: live_loop_test.py [папка_модели] [файл.wav]; MON=0 отключает монитор. Applio на время теста остановить.
"""

import os
import sys
import threading
import time

import librosa
import numpy as np
import sounddevice as sd

from common import cable_name, find_device, headphones_name, model_files, source_wav, use_applio, virtual_mic_name

pth, idx = model_files(sys.argv[1] if len(sys.argv) > 1 else None)
src_path = source_wav(sys.argv[2] if len(sys.argv) > 2 else None)
use_applio()

from rvc.realtime.callbacks import AudioCallbacks  # noqa: E402

USE_MONITOR = os.environ.get("MON", "1") == "1"
SR, CHUNK_MS = 48000, 150
block = int(CHUNK_MS * SR / 1000)

cb = AudioCallbacks(
    pass_through=False, block_frame=block, cross_fade_overlap_size=0.05, extra_convert_size=2.5,
    model_path=pth, index_path=idx,
    f0_method="rmvpe", embedder_model="contentvec", embedder_model_custom=None, silent_threshold=-90,
    f0_up_key=14, index_rate=0.75, protect=0.5, volume_envelope=0.0,
    f0_autotune=False, f0_autotune_strength=1.0, proposed_pitch=False, proposed_pitch_threshold=255.0,
    input_audio_gain=1.0, output_audio_gain=1.0, monitor_audio_gain=0.0, monitor=USE_MONITOR,
    vad_enabled=False, vad_sensitivity=3, vad_frame_ms=30, sid=0, clean_audio=False, clean_strength=0.5,
    post_process=False, record_audio=False, record_audio_path=None, export_format="WAV",
    audio_sample_rate=SR, kwargs={},
)
cb.audio.start(
    input_device_id=find_device(virtual_mic_name(), "in"), output_device_id=find_device(cable_name("out"), "out"),
    output_monitor_id=find_device(headphones_name(), "out"), exclusive_mode=False,
    asio_input_channel=-1, asio_output_channel=-1, asio_output_monitor_channel=-1,
    block_frame=block, audio_sample_rate=SR, asio_output_stereo=True,
)

src, _ = librosa.load(src_path, sr=SR, mono=True)
src = np.concatenate([np.zeros(SR * 4, dtype=np.float32), src, np.zeros(SR, dtype=np.float32)])
rec = []


def capture():
    rec.append(sd.rec(len(src), samplerate=SR, channels=1, dtype="float32", device=find_device(cable_name(), "in"), blocking=True))


t = threading.Thread(target=capture)
t.start()
time.sleep(0.2)
with sd.OutputStream(device=find_device(virtual_mic_name(), "out"), samplerate=SR, channels=2, dtype="float32") as o:
    o.write(np.repeat(src[:, None], 2, axis=1))
t.join()
cb.audio.stop()


def gaps(y):
    w = SR // 20
    n = len(y) // w
    e = np.sqrt((y[: n * w].reshape(n, w) ** 2).mean(1))
    e = e[int(4.5 * 20):]
    return float((e < e.max() * 0.02).mean() * 100), float(np.sqrt((y[int(4.5 * SR):] ** 2).mean()))


g_src, r_src = gaps(src)
g_out, r_out = gaps(rec[0][:, 0])
print("RESULT монитор=%s | исходник: пауз %.1f%% rms %.4f | в кабеле: пауз %.1f%% rms %.4f"
      % ("вкл" if USE_MONITOR else "выкл", g_src, r_src, g_out, r_out))
os._exit(0)
