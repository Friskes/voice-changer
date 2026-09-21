"""Собирает по одному файлу-прослушке на каждый голос-кандидат и оценивает его тон, возраст и пол.

Запуск: make_audition.py <папка>, где каждая подпапка — кандидат с несколькими WAV. Итог — в logs/audition.
"""

import glob
import os
import sys

import librosa
import numpy as np
import soundfile as sf

from agegender import analyze
from common import LOGS
from voicemetrics import f0_median

if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
    raise SystemExit(__doc__)

OUT = str(LOGS / "audition")
SR = 32000
os.makedirs(OUT, exist_ok=True)

gap = np.zeros(int(SR * 0.4), dtype=np.float32)
print("%-40s %-8s %-8s %s" % ("кандидат", "F0", "возраст", "female"))
for name in sorted(os.listdir(sys.argv[1])):
    files = sorted(glob.glob(os.path.join(sys.argv[1], name, "*.wav")))[:7]
    if not files:
        continue
    parts = []
    for f in files:
        y, _ = librosa.load(f, sr=SR, mono=True)
        y = y / (np.abs(y).max() + 1e-9) * 0.7
        parts += [y.astype(np.float32), gap]
    dst = os.path.join(OUT, name + ".wav")
    sf.write(dst, np.concatenate(parts), SR)
    r = analyze(dst)
    print("%-40s %-8.0f %-8.0f %.2f" % (name, f0_median(dst), r["age"], r["female"]))
