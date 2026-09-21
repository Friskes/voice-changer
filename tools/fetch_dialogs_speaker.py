"""Качает из Dialogs (langswap, OpenRAIL) ~N минут одной актрисы в папку датасета Applio.

Запуск: python fetch_dialogs_speaker.py <M|S> <минут> <папка_датасета> [dry]
"""
import csv, io, json, os, random, re, sys, urllib.request

REPO = "https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations"
API = "https://huggingface.co/api/datasets/langswap/dialogs-ru-emotional-conversations/tree/main/wavs?limit=1000"
SHARE = {"happy": 0.55, "neutral": 0.35, "surprise": 0.10}


def repo_files():
    names, url = set(), API
    while url:
        with urllib.request.urlopen(url) as r:
            names |= {d["path"] for d in json.load(r)}
            m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link") or "")
        url = m.group(1) if m else None
    return names


def main(speaker, minutes, out_dir, dry=False):
    meta = urllib.request.urlopen(REPO + "/resolve/main/metadata.csv").read().decode("utf-8")
    present = repo_files()
    rows = [r for r in csv.DictReader(io.StringIO(meta), delimiter="|")
            if r["speaker_id"] == speaker and r["emotion"] in SHARE
            and 2.5 <= float(r["duration"]) <= 12 and r["audio_path"] in present]
    random.Random(42).shuffle(rows)
    picked, got = [], {e: 0.0 for e in SHARE}
    for r in rows:
        e = r["emotion"]
        if got[e] < minutes * 60 * SHARE[e]:
            picked.append(r); got[e] += float(r["duration"])
    print("clips:", len(picked), "minutes:", {e: round(s / 60, 1) for e, s in got.items()})
    if dry:
        return
    os.makedirs(out_dir, exist_ok=True)
    for i, r in enumerate(picked, 1):
        dst = os.path.join(out_dir, os.path.basename(r["audio_path"]))
        if not os.path.exists(dst) or os.path.getsize(dst) < 2048:
            urllib.request.urlretrieve(f"{REPO}/resolve/main/{r['audio_path']}", dst)
        if i % 50 == 0:
            print(i, "/", len(picked), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), sys.argv[3], dry=len(sys.argv) > 4)
