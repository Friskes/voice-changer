"""Общие пути, устройства и модель для скриптов из tools/.

Устройства и модель по умолчанию берутся из конфига Applio — то, что выбрано во вкладке Realtime.
Переопределяются переменными окружения VC_MIC, VC_CABLE, VC_VIRTUAL_MIC, VC_HEADPHONES (часть имени).
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPLIO = ROOT / "Applio"
LOGS = ROOT / "logs"
MY_VOICE = LOGS / "refs" / "my_voice.wav"

os.environ.setdefault("HF_HOME", str(ROOT / "hf-cache"))


def use_applio():
    """Переходит в папку Applio и добавляет её в sys.path: его модули ищут файлы относительно cwd."""
    if not (APPLIO / "core.py").exists():
        raise SystemExit("Applio не найден в %s — сначала запусти install.bat" % APPLIO)
    os.chdir(APPLIO)
    sys.path.append(str(APPLIO))


def realtime_config():
    try:
        text = (APPLIO / "assets" / "config.json").read_text(encoding="utf-8")
        return json.loads(text).get("realtime", {})
    except (OSError, ValueError):
        return {}


def _configured(key):
    """Имя устройства из конфига Applio без порядкового номера и названия аудио-API."""
    return re.sub(r"^\d+:\s*|\s*\([^()]*\)$", "", realtime_config().get(key) or "")


def _name(env, fallback, what):
    name = os.environ.get(env) or fallback
    if not name:
        raise SystemExit(
            "Не знаю, где %s: выбери устройства во вкладке Realtime в Applio и нажми «Старт» "
            "либо задай переменную окружения %s (часть имени устройства)." % (what, env)
        )
    return name


def mic_name():
    return _name("VC_MIC", _configured("input_device"), "микрофон")


def cable_name(side="in"):
    """Кабель, в который Applio отдаёт голос; у VB-CABLE пишущая сторона зовётся Output, а не Input."""
    name = _configured("output_device")
    if side == "in" and name.startswith("CABLE"):
        name = name.replace(" Input", " Output")
    return _name("VC_CABLE", name, "виртуальный кабель")


def headphones_name():
    return _name("VC_HEADPHONES", _configured("monitor_device"), "наушники")


def virtual_mic_name():
    return _name("VC_VIRTUAL_MIC", "", "второй виртуальный кабель")


def find_device(part, kind):
    """Индекс WASAPI-устройства по части имени; kind: "in" — запись, "out" — воспроизведение."""
    import sounddevice as sd

    apis = sd.query_hostapis()
    field = "max_input_channels" if kind == "in" else "max_output_channels"
    for i, d in enumerate(sd.query_devices()):
        if d[field] > 0 and "WASAPI" in apis[d["hostapi"]]["name"] and part.lower() in d["name"].lower():
            return i
    raise SystemExit("нет WASAPI-устройства «%s» (%s)" % (part, "запись" if kind == "in" else "воспроизведение"))


def model_files(folder=None):
    """Пути (.pth, .index): из Applio/logs/<folder> либо модель, выбранная во вкладке Realtime."""
    if folder:
        d = APPLIO / "logs" / folder
        pth = sorted(
            (p for p in d.glob("*.pth") if not p.name.startswith(("G_", "D_"))),
            key=lambda p: p.stat().st_mtime,
        )
        if not pth:
            raise SystemExit("в %s нет файла модели .pth" % d)
        idx = sorted(d.glob("*.index"))
        return str(pth[-1]), str(idx[0]) if idx else ""
    cfg = realtime_config()
    if not cfg.get("model_file"):
        raise SystemExit("Модель не выбрана: укажи папку модели аргументом или выбери модель в Applio.")
    idx = cfg.get("index_file") or ""
    return str(APPLIO / cfg["model_file"]), str(APPLIO / idx) if idx else ""


def source_wav(path=None):
    """Запись речи для тестов: явный путь либо образец, записанный record-my-voice.bat."""
    src = Path(path).resolve() if path else MY_VOICE
    if not src.exists():
        raise SystemExit("нет файла %s — запиши голос через record-my-voice.bat или передай путь к WAV" % src)
    return str(src)
