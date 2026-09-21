"""Прогоняет файл через realtime-движок Applio блоками, как это делает живой поток.

Отделяет проблемы движка/модели/настроек от проблем аудиоустройств: здесь устройств нет вовсе.
Без аргументов берёт модель, выбранную в Applio, и запись из record-my-voice.bat.
"""

import argparse
import os

import librosa
import numpy as np
import soundfile as sf

from common import LOGS, model_files, source_wav, use_applio

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--model", help="папка модели в Applio/logs (по умолчанию — выбранная в Applio)")
ap.add_argument("--src", help="WAV с речью (по умолчанию logs/refs/my_voice.wav)")
ap.add_argument("--chunk", type=int, default=100, help="размер блока, мс")
ap.add_argument("--pitch", type=int, default=14)
ap.add_argument("--envelope", type=float, default=0.0, help="Volume Envelope")
ap.add_argument("--index-rate", type=float, default=0.75)
ap.add_argument("--f0", default="rmvpe")
ap.add_argument("--gain", type=float, default=1.0, help="усиление входа")
ap.add_argument("--extra", type=float, default=2.5, help="Extra Conversion Size, с")
ap.add_argument("--threshold", type=int, default=-90, help="Silence Threshold, дБ")
ap.add_argument("--vad", action="store_true")
args = ap.parse_args()

pth, idx = model_files(args.model)
src = source_wav(args.src)
use_applio()

from rvc.realtime.core import AUDIO_SAMPLE_RATE, VoiceChanger  # noqa: E402

y, _ = librosa.load(src, sr=AUDIO_SAMPLE_RATE, mono=True)
y = (y * args.gain).astype(np.float32)

block = int(args.chunk * AUDIO_SAMPLE_RATE / 1000)
vc = VoiceChanger(
    block_frame=block, cross_fade_overlap_size=0.05, extra_convert_size=args.extra,
    model_path=pth, index_path=idx, f0_method=args.f0, embedder_model="contentvec",
    silent_threshold=args.threshold, vad_enabled=args.vad,
)

out, times = [], []
for i in range(0, len(y) - block, block):
    res, vol, perf = vc.on_request(
        y[i : i + block], f0_up_key=args.pitch, index_rate=args.index_rate, protect=0.5,
        volume_envelope=args.envelope,
    )
    res = res.detach().cpu().numpy() if hasattr(res, "detach") else np.asarray(res)
    out.append(res.astype(np.float32).ravel())
    times.append(perf[1])

o = np.concatenate(out)
name = os.path.splitext(os.path.basename(pth))[0]
tag = "%s_c%d_ve%02d_ir%02d_%s_g%.0f" % (
    name, args.chunk, int(args.envelope * 100), int(args.index_rate * 100), args.f0, args.gain * 100,
)
dst = LOGS / "stream_sim" / (tag + ".wav")
dst.parent.mkdir(parents=True, exist_ok=True)
sf.write(str(dst), o, AUDIO_SAMPLE_RATE)

win = AUDIO_SAMPLE_RATE // 20
warm = int(3.0 * 20)


def quiet_share(sig):
    """Доля окон по 50 мс тише 2% от пика; паузы речи сюда тоже входят, поэтому вход и выход сравниваются."""
    n = len(sig) // win
    env = np.sqrt((sig[: n * win].reshape(n, win) ** 2).mean(axis=1))[warm:]
    return float((env < env.max() * 0.02).mean() * 100)


t = np.array(times[5:])
print(
    "RESULT %-46s in_rms %.4f out_rms %.4f out_peak %.3f | тихих окон: вход %4.1f%% -> выход %4.1f%% | инференс %.0f мс (p95 %.0f) при блоке %d мс"
    % (tag, float(np.sqrt((y**2).mean())), float(np.sqrt((o[warm * win:] ** 2).mean())), float(np.abs(o).max()),
       quiet_share(y), quiet_share(o), t.mean(), np.percentile(t, 95), args.chunk)
)
print("результат: %s" % dst)
