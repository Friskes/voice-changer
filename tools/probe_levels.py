"""Одновременно пишет микрофон и виртуальный кабель и печатает огибающие — видно, где рвётся звук."""

import sys
import time

import numpy as np
import sounddevice as sd

from common import cable_name, find_device, mic_name

DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
SR = 48000

bufs = {"mic": [], "cable": []}


def cb(key):
    def _cb(indata, frames, t, status):
        bufs[key].append(indata[:, 0].copy())
    return _cb


streams = [
    sd.InputStream(device=find_device(mic_name(), "in"), samplerate=SR, channels=1, dtype="float32", callback=cb("mic")),
    sd.InputStream(device=find_device(cable_name(), "in"), samplerate=SR, channels=1, dtype="float32", callback=cb("cable")),
]
for s in streams:
    s.start()
time.sleep(DUR)
for s in streams:
    s.stop()
    s.close()

win = SR // 10
env = {}
for k, chunks in bufs.items():
    y = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    n = len(y) // win
    env[k] = np.sqrt((y[: n * win].reshape(n, win) ** 2).mean(axis=1)) if n else np.zeros(1)
    print("%-6s peak %.4f  rms %.5f" % (k, float(np.abs(y).max()), float(np.sqrt((y**2).mean()))))


def bar(v, ref):
    return "#" * int(min(30, 30 * v / ref)) if ref > 0 else ""


n = min(len(env["mic"]), len(env["cable"]))
mref, lref = max(env["mic"].max(), 1e-6), max(env["cable"].max(), 1e-6)
print("\n t,с   микрофон                        | кабель (что уходит собеседнику)")
for i in range(n):
    print("%4.1f  %-30s | %-30s" % (i / 10, bar(env["mic"][i], mref), bar(env["cable"][i], lref)))

active = env["mic"][:n] > mref * 0.15
if active.any():
    dropped = (env["cable"][:n][active] < lref * 0.05).mean() * 100
    print("\nпока ты говоришь, на выходе тишина в %.0f%% отрезков" % dropped)
