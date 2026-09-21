"""Накладывает патчи из patches/ на Applio. Повторный запуск безопасен, --revert откатывает.

Свой разбор unified diff вместо git apply: файлы Applio в архиве с CRLF, а git на машине может не быть.
"""

import re
import shutil
import sys

from common import APPLIO, ROOT

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @@")


def parse(text):
    """Возвращает {путь: [(строка_начала, старые_строки, новые_строки), ...]} по всем файлам патча."""
    files, lines, i = {}, text.splitlines(), 0
    while i < len(lines):
        m = HUNK.match(lines[i])
        if lines[i].startswith("+++ "):
            hunks = files.setdefault(re.sub(r"^b/", "", lines[i][4:].split("\t")[0].strip()), [])
        elif m:
            n_old = int(m.group(2)) if m.group(2) is not None else 1
            n_new = int(m.group(3)) if m.group(3) is not None else 1
            old, new = [], []
            while len(old) < n_old or len(new) < n_new:
                i += 1
                tag, body = lines[i][:1], lines[i][1:]
                if tag == "\\":
                    continue
                if tag != "+":
                    old.append(body)
                if tag != "-":
                    new.append(body)
            hunks.append((int(m.group(1)) - 1, old, new))
        i += 1
    return files


def locate(lines, block, hint):
    """Индекс блока в файле, ближайший к месту из заголовка hunk, либо None."""
    hits = [k for k in range(len(lines) - len(block) + 1) if lines[k : k + len(block)] == block]
    return min(hits, key=lambda k: abs(k - hint)) if hits else None


def patch_text(raw, hunks):
    """Возвращает новый текст либо None, если патч уже наложен. Бросает ValueError, если файл не тот."""
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    done, shift = 0, 0
    for start, old, new in hunks:
        at = locate(lines, old, start + shift)
        if at is None:
            if locate(lines, new, start + shift) is None:
                raise ValueError("не нахожу место для правки около строки %d" % (start + 1))
            done += 1
            continue
        lines[at : at + len(old)] = new
        shift += len(new) - len(old)
    if done == len(hunks):
        return None
    if done:
        raise ValueError("патч наложен частично — верни файл из .orig и запусти заново")
    return nl.join(lines)


def main(revert):
    """Сначала считает результат по всем патчам в памяти (один файл могут править несколько), потом пишет на диск."""
    texts, changed, report = {}, set(), []
    for patch in sorted((ROOT / "patches").glob("*.patch"), reverse=revert):
        for rel, hunks in parse(patch.read_text(encoding="utf-8")).items():
            if revert:
                hunks = [(start, new, old) for start, old, new in hunks]
            target = APPLIO / rel
            try:
                if target not in texts:
                    texts[target] = target.read_bytes().decode("utf-8")
                text = patch_text(texts[target], hunks)
            except (OSError, ValueError) as e:
                raise SystemExit(
                    "%s: %s: %s\nПатчи рассчитаны на Applio 3.6.5 — проверь версию в Applio/assets/config.json."
                    % (patch.name, rel, e)
                )
            if text is not None:
                texts[target] = text
                changed.add(target)
            report.append((patch.name, target, text is not None))
    for target in changed:
        backup = target.with_name(target.name + ".orig")
        if not revert and not backup.exists():
            shutil.copy2(target, backup)
        target.write_bytes(texts[target].encode("utf-8"))
    for name, target, did in report:
        status = ("откатан" if revert else "наложен") if did else ("нечего откатывать" if revert else "уже наложен")
        print("%-30s %s — %s" % (name, target.relative_to(APPLIO), status))


if __name__ == "__main__":
    main("--revert" in sys.argv[1:])
