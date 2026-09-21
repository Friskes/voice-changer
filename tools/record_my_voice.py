"""Записывает образец голоса для подбора модели и настроек.

Запускать через record-my-voice.bat. Пишет 30 секунд с выбранного микрофона
в logs/refs/my_voice.wav и подсказывает значение Pitch для Applio.
"""

import sys

import numpy as np
import sounddevice as sd
import soundfile as sf

from common import MY_VOICE

SR = 48000
DUR = 30

FRAZY = [
    "Один справа от бочки, я захожу на длинную.",
    "Прикройте меня, у них снайпер на балконе.",
    "Беру точку А, кидаю дым, заходим вместе.",
    "Осторожно, сзади может быть второй.",
    "Да ладно, серьёзно? Я вообще не ожидала такого.",
    "Ну всё, ребят, я пошла, удачи вам там.",
]

devs = sd.query_devices()
apis = sd.query_hostapis()
mics = [
    (i, d["name"], apis[d["hostapi"]]["name"])
    for i, d in enumerate(devs)
    if d["max_input_channels"] > 0 and apis[d["hostapi"]]["name"] == "Windows WASAPI"
]

if not mics:
    print("Микрофонов WASAPI не найдено.")
    sys.exit(1)

print("Доступные микрофоны:\n")
for n, (i, name, api) in enumerate(mics, 1):
    print("  %d) %s" % (n, name))

choice = input("\nНомер микрофона (Enter — первый): ").strip()
idx = mics[int(choice) - 1][0] if choice else mics[0][0]
print("\nПишем с: %s" % devs[idx]["name"])

print("\nПрочитай вслух своим обычным игровым голосом, не наигрывая:\n")
for f in FRAZY:
    print("   " + f)

input("\nEnter — старт записи на %d секунд..." % DUR)
print("ЗАПИСЬ ПОШЛА")

rec = sd.rec(int(SR * DUR), samplerate=SR, channels=1, dtype="float32", device=idx)
for s in range(DUR, 0, -1):
    sd.sleep(1000)
    print("  осталось %2d с" % (s - 1), end="\r")
sd.wait()
print("\nготово")

MY_VOICE.parent.mkdir(parents=True, exist_ok=True)
sf.write(str(MY_VOICE), rec, SR)

peak = float(np.abs(rec).max())
rms = float(np.sqrt((rec**2).mean()))
print("\nфайл: %s" % MY_VOICE)
print("пик %.3f, rms %.4f" % (peak, rms))
if peak < 0.05:
    print("ТИХО. Добавь громкости микрофона и перезапиши.")
elif peak > 0.99:
    print("КЛИППИНГ. Убавь громкость микрофона и перезапиши.")
else:
    print("уровень нормальный")

import librosa  # noqa: E402

y16 = librosa.resample(rec[:, 0], orig_sr=SR, target_sr=16000)
f0 = librosa.yin(y16, fmin=60, fmax=400, sr=16000, frame_length=1024)
env = librosa.feature.rms(y=y16, frame_length=1024, hop_length=256)[0]
n = min(len(f0), len(env))
voiced = f0[:n][env[:n] > np.percentile(env[:n], 50)]
if voiced.size:
    my_f0 = float(np.median(voiced))
    print("\nТвой средний тон: %.0f Гц" % my_f0)
    for target, label in ((235, "обычный женский"), (255, "повыше, «милее»")):
        print("  Pitch в Applio для %s (%d Гц): %+d" % (label, target, round(12 * np.log2(target / my_f0))))
