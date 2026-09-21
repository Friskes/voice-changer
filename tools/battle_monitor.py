"""Боевой мониторинг: пишет огибающие микрофона и виртуального кабеля плюс загрузку GPU, затем ищет провалы.

Провал = ты говоришь, а в кабеле (то, что слышит собеседник) в этот момент тишина.
Запуск: battle_monitor.py <секунд>
"""

import subprocess
import sys
import threading
import time

import numpy as np
import sounddevice as sd

from common import cable_name, find_device, mic_name

DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 180
SR, WIN = 48000, 2400  # окно 50 мс

env = {"mic": [], "out": []}
rest = {"mic": np.zeros(0, dtype=np.float32), "out": np.zeros(0, dtype=np.float32)}


def cb(key):
    def _cb(indata, frames, t, status):
        y = np.concatenate([rest[key], indata[:, 0]])
        n = len(y) // WIN
        if n:
            env[key].extend(np.sqrt((y[: n * WIN].reshape(n, WIN) ** 2).mean(axis=1)).tolist())
        rest[key] = y[n * WIN:]
    return _cb


gpu = []


def gpu_poll():
    end = time.time() + DUR
    while time.time() < end:
        try:
            o = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
            gpu.append(int(o.splitlines()[0]))
        except Exception:
            gpu.append(-1)
        time.sleep(1)


streams = [
    sd.InputStream(device=find_device(mic_name(), "in"), samplerate=SR, channels=1, dtype="float32", callback=cb("mic")),
    sd.InputStream(device=find_device(cable_name(), "in"), samplerate=SR, channels=1, dtype="float32", callback=cb("out")),
]
th = threading.Thread(target=gpu_poll, daemon=True)
th.start()
for s in streams:
    s.start()
time.sleep(DUR)
for s in streams:
    s.stop()
    s.close()

n = min(len(env["mic"]), len(env["out"]))
mic, out = np.array(env["mic"][:n]), np.array(env["out"][:n])
g = np.array([x for x in gpu if x >= 0] or [0])

print("длительность %d с | GPU: средняя %d%%, медиана %d%%, макс %d%%, доля времени выше 95%%: %d%%"
      % (n // 20, g.mean(), np.median(g), g.max(), (g >= 95).mean() * 100))
print("микрофон: пик огибающей %.4f | кабель: пик огибающей %.4f" % (mic.max(), out.max()))

mic_thr = max(np.percentile(mic, 95) * 0.2, 0.004)
out_thr = max(np.percentile(out, 95) * 0.06, 0.0008)
speech = mic > mic_thr
print("речи в микрофоне: %.0f с из %d" % (speech.sum() / 20, n // 20))
if speech.sum() < 40:
    print("речи слишком мало для анализа")
    sys.exit(0)

a = (mic > mic_thr).astype(float) - (mic > mic_thr).mean()
b = (out > out_thr).astype(float) - (out > out_thr).mean()
best_lag, best = 0, -1
for lag in range(0, 40):
    c = float((a[: n - lag] * b[lag:]).sum())
    if c > best:
        best, best_lag = c, lag
print("задержка микрофон -> кабель: ~%d мс" % (best_lag * 50))

# Говорящие окна без краёв фраз: начало и конец слова естественно тише.
core = speech.copy()
core[1:] &= speech[:-1]
core[:-1] &= speech[1:]
idx = np.where(core)[0]
idx = idx[idx + best_lag < n]
silent = out[idx + best_lag] < out_thr
print("провалов внутри речи: %.1f%% окон (%d из %d)" % (silent.mean() * 100, silent.sum(), len(idx)))

runs, cur = [], 0
for v in silent:
    if v:
        cur += 1
    elif cur:
        runs.append(cur)
        cur = 0
if cur:
    runs.append(cur)
long_runs = [r for r in runs if r >= 2]
print("заметных провалов (>=100 мс): %d шт, самый длинный %d мс" % (len(long_runs), max(long_runs or [0]) * 50))

if len(g) > 5 and silent.any():
    sec = ((idx[silent] + best_lag) // 20).clip(0, len(g) - 1)
    print("GPU в моменты провалов: средняя %d%% (в остальное время %d%%)" % (g[sec].mean(), g.mean()))

lvl = out[idx + best_lag][~silent]
if lvl.size:
    print("громкость выхода при речи: медиана %.4f (вход %.4f)" % (np.median(lvl), np.median(mic[idx])))
