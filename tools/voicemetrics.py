"""Метрики «женскости» голоса: F0 и форманты F1-F3.

Форманты берутся по LPC с отбраковкой корней по ширине полосы — без неё оценка
цепляется за гармоники основного тона, что на высоком голосе даёт мусор.
"""

import warnings

import librosa
import numpy as np

warnings.filterwarnings("ignore")

SR = 16000
MAX_BW = 400.0


def _voiced_frames(y, frame=512, hop=256, pct=60):
    rms = librosa.feature.rms(y=y, frame_length=frame, hop_length=hop)[0]
    thr = np.percentile(rms, pct)
    for i in range(len(rms)):
        if rms[i] < thr:
            continue
        seg = y[i * hop : i * hop + frame]
        if len(seg) == frame:
            yield seg


def formants(path, n=3):
    y, _ = librosa.load(path, sr=SR, mono=True)
    y = librosa.effects.preemphasis(y, coef=0.97)
    order = 2 + SR // 1000
    found = [[] for _ in range(n)]
    for seg in _voiced_frames(y):
        try:
            a = librosa.lpc(seg * np.hamming(len(seg)), order=order)
        except Exception:
            continue
        roots = np.roots(a)
        roots = roots[(np.imag(roots) > 0) & (np.abs(roots) < 1.0)]
        if roots.size == 0:
            continue
        freq = np.abs(np.angle(roots)) * SR / (2 * np.pi)
        bw = -0.5 * (SR / (2 * np.pi)) * np.log(np.abs(roots))
        keep = (bw < MAX_BW) & (freq > 90) & (freq < 4500)
        freq = np.sort(freq[keep])
        for k in range(min(n, len(freq))):
            found[k].append(freq[k])
    return [float(np.median(f)) if f else float("nan") for f in found]


def f0_median(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    f0 = librosa.yin(y, fmin=60, fmax=500, sr=SR, frame_length=1024)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    n = min(len(f0), len(rms))
    v = f0[:n][rms[:n] > np.percentile(rms[:n], 45)]
    return float(np.median(v)) if v.size else float("nan")


def tract_ratio(out_formants, src_formants):
    """Во сколько раз форманты выше исходных. ~1.15-1.20 = женский тракт."""
    rs = [o / s for o, s in zip(out_formants, src_formants) if not (np.isnan(o) or np.isnan(s))]
    return float(np.mean(rs)) if rs else float("nan")
