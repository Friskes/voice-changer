"""Конвертирует запись голоса пользователя при разной высоте тона и оценивает пол и возраст результата.

Запуск: my_voice_pitch.py [папка_модели] [файл.wav]. Результаты — в logs/my_voice_test.
"""

import os
import sys

from common import LOGS, model_files, source_wav, use_applio

pth, idx = model_files(sys.argv[1] if len(sys.argv) > 1 else None)
SRC = source_wav(sys.argv[2] if len(sys.argv) > 2 else None)
OUT = str(LOGS / "my_voice_test")
os.makedirs(OUT, exist_ok=True)
use_applio()

from agegender import analyze  # noqa: E402
from voicemetrics import f0_median  # noqa: E402

from core import run_infer_script  # noqa: E402

r = analyze(SRC)
print("твой голос: F0 %.0f Гц, возраст по классификатору %.0f" % (f0_median(SRC), r["age"]))
print("\n%-22s %-8s %-9s %s" % ("высота тона", "F0", "возраст", "female"))
for pitch in (10, 11, 12, 13, 14, 15, 16):
    dst = os.path.join(OUT, "pitch%+d.wav" % pitch)
    run_infer_script(
        pitch=pitch, index_rate=0.75, volume_envelope=0.0, protect=0.5, f0_method="rmvpe",
        input_path=SRC, output_path=dst, pth_path=pth, index_path=idx, split_audio=False,
        f0_autotune=False, f0_autotune_strength=1.0, proposed_pitch=False, proposed_pitch_threshold=255.0,
        clean_audio=False, clean_strength=0.5, export_format="WAV", embedder_model="contentvec",
    )
    a = analyze(dst)
    print("%-22s %-8.0f %-9.0f %.2f" % ("%+d" % pitch, f0_median(dst), a["age"], a["female"]))
