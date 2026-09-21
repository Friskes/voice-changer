"""Обучение RVC-модели на голосе актрисы из корпуса Dialogs.

Запуск: train_voice.py [M|S] [имя_модели] [эпох]. Ход пишется в logs/train-<имя>.log.
"""

import hashlib
import os
import subprocess
import sys
import time
import urllib.request

from common import APPLIO, LOGS, use_applio

SPK = sys.argv[1] if len(sys.argv) > 1 else "M"
NAME = sys.argv[2] if len(sys.argv) > 2 else "ru-masha"
EPOCHS = sys.argv[3] if len(sys.argv) > 3 else "200"
MINUTES = "45"
BATCH = "8"
CORES = str(min(8, os.cpu_count() or 1))

PRETRAIN_URL = "https://huggingface.co/MUSTAR/SnowieV3.1-40k/resolve/main/"
PRETRAIN_SHA256 = {
    "G_SnowieV3.1_40k.pth": "95aeacf9ac4c39830fc19bec5f11d780734f73bd53ce681d7f21b891f7da69e7",
    "D_SnowieV3.1_40k.pth": "33eb0b69d2eb1980105b044d7381d2c317652f011f7fa685a599aee846a68592",
}

use_applio()
PRE = APPLIO / "rvc" / "models" / "pretraineds" / "custom"
DATASET = "assets/datasets/" + NAME
LOGS.mkdir(exist_ok=True)
LOG = LOGS / ("train-%s.log" % NAME)


def step(title):
    line = "=== %s %s" % (time.strftime("%H:%M:%S"), title)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(*cmd):
    with open(LOG, "a", encoding="utf-8") as f:
        code = subprocess.run([sys.executable, *cmd], stdout=f, stderr=subprocess.STDOUT).returncode
    if code:
        raise SystemExit("шаг завершился с ошибкой, подробности в %s" % LOG)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_pretrain():
    """Качает претрейн и сверяет SHA256: .pth — это pickle, подменённый файл выполнил бы чужой код."""
    PRE.mkdir(parents=True, exist_ok=True)
    for name, want in PRETRAIN_SHA256.items():
        dst = PRE / name
        if not dst.exists():
            print("    качаю %s" % name, flush=True)
            part = dst.with_suffix(".part")
            urllib.request.urlretrieve(PRETRAIN_URL + name, part)
            os.replace(part, dst)
        if sha256(dst) != want:
            raise SystemExit("контрольная сумма %s не совпала — удали файл и запусти заново" % dst)


step("1/5 данные")
run(os.path.join(os.path.dirname(__file__), "fetch_dialogs_speaker.py"), SPK, MINUTES, str(APPLIO / DATASET))

step("2/5 претрейн")
fetch_pretrain()

step("3/5 preprocess")
run("core.py", "preprocess", "--model-name", NAME, "--dataset-path", DATASET, "--sample-rate", "40000",
    "--cpu-cores", CORES, "--cut-preprocess", "Automatic", "--process-effects", "--chunk-len", "3.0",
    "--overlap-len", "0.3")

step("4/5 extract")
run("core.py", "extract", "--model-name", NAME, "--f0-method", "rmvpe", "--cpu-cores", CORES, "--gpu", "0",
    "--sample-rate", "40000", "--embedder-model", "contentvec", "--include-mutes", "2")

step("5/5 train %s эпох" % EPOCHS)
run("core.py", "train", "--model-name", NAME, "--vocoder", "HiFi-GAN", "--save-every-epoch", "25",
    "--save-only-latest", "--total-epoch", EPOCHS, "--sample-rate", "40000", "--batch-size", BATCH, "--gpu", "0",
    "--pretrained", "--custom-pretrained",
    "--g-pretrained-path", "rvc/models/pretraineds/custom/G_SnowieV3.1_40k.pth",
    "--d-pretrained-path", "rvc/models/pretraineds/custom/D_SnowieV3.1_40k.pth",
    "--cache-data-in-gpu", "--index-algorithm", "Auto")

step("ГОТОВО")
out = APPLIO / "logs" / NAME
for p in sorted(out.glob("*.index")) + sorted(p for p in out.glob("*.pth") if not p.name.startswith(("G_", "D_"))):
    print("  %4d МБ  %s" % (p.stat().st_size >> 20, p))
