"""Оценка пола и возраста голоса моделью audeering wav2vec2 age-gender.

Выдаёт вероятности female/male/child и оценку возраста в годах — это ближе к тому,
как голос воспринимается на слух, чем ручные замеры формант.
"""

import os

import common  # noqa: F401

import librosa  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from transformers import Wav2Vec2Processor  # noqa: E402
from transformers.models.wav2vec2.modeling_wav2vec2 import (  # noqa: E402
    Wav2Vec2Model,
    Wav2Vec2PreTrainedModel,
)

NAME = "audeering/wav2vec2-large-robust-24-ft-age-gender"


class ModelHead(nn.Module):
    def __init__(self, config, num_labels):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, num_labels)

    def forward(self, x):
        x = self.dropout(x)
        x = torch.tanh(self.dense(x))
        x = self.dropout(x)
        return self.out_proj(x)


class AgeGenderModel(Wav2Vec2PreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.wav2vec2 = Wav2Vec2Model(config)
        self.age = ModelHead(config, 1)
        self.gender = ModelHead(config, 3)
        self.post_init()

    def forward(self, input_values):
        hidden = self.wav2vec2(input_values)[0].mean(dim=1)
        return self.age(hidden), torch.softmax(self.gender(hidden), dim=1)


_cache = {}


def _load():
    if not _cache:
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        _cache["proc"] = Wav2Vec2Processor.from_pretrained(NAME)
        _cache["model"] = AgeGenderModel.from_pretrained(NAME).to(dev).eval()
        _cache["dev"] = dev
    return _cache["proc"], _cache["model"], _cache["dev"]


def analyze(path):
    """Возвращает dict: female, male, child (вероятности) и age (лет)."""
    proc, model, dev = _load()
    y, _ = librosa.load(path, sr=16000, mono=True)
    x = proc(y, sampling_rate=16000, return_tensors="pt")["input_values"].to(dev)
    with torch.no_grad():
        age, gender = model(x)
    g = gender[0].cpu().numpy()
    return {
        "female": float(g[0]),
        "male": float(g[1]),
        "child": float(g[2]),
        "age": float(age[0, 0].cpu()) * 100,
    }


if __name__ == "__main__":
    import glob
    import sys

    for pattern in sys.argv[1:]:
        for p in sorted(glob.glob(pattern)):
            r = analyze(p)
            print(
                "%-58s female %.2f  male %.2f  child %.2f  возраст %4.0f"
                % (os.path.basename(p)[:58], r["female"], r["male"], r["child"], r["age"])
            )
