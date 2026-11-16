"""Разбиение набора пассажиропотока на исходную часть и порции «новых» данных.

Делим по времени: исходная часть — с I квартала 2021 по II квартал 2024 года,
дальше каждые полгода (две квартальные публикации) — отдельная порция.
Файл в data/raw не изменяется. Запуск: python scripts/split_batches.py
"""
import csv
import hashlib
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PARAMS = yaml.safe_load((ROOT / "params.yaml").read_text(encoding="utf-8"))["split"]
RAW = ROOT / "data" / "raw" / PARAMS["source_file"]
QUARTER = {"I квартал": 1, "II квартал": 2, "III квартал": 3, "IV квартал": 4}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # вторая строка файла дублирует заголовки по-русски
    df = pd.read_csv(RAW, sep=";", skiprows=[1], encoding="utf-8")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    period = df["Year"] * 10 + df["Quarter"].map(QUARTER)

    out = []
    initial = df[period <= PARAMS["initial_until"]]
    path = ROOT / "data" / "initial" / "passenger_flow_initial.csv"
    initial.to_csv(path, sep=";", index=False, encoding="utf-8")
    out.append(path)

    for i, (start, end) in enumerate(PARAMS["batches"], 1):
        part = df[(period >= start) & (period <= end)]
        path = ROOT / "data" / "incoming" / f"batch_{i:02d}.csv"
        part.to_csv(path, sep=";", index=False, encoding="utf-8")
        out.append(path)

    assert sum(len(pd.read_csv(p, sep=";")) for p in out) == len(df), "строки потеряны"

    # файл-описание: имя, число строк, контрольная сумма, источник
    with open(ROOT / "data" / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["file", "rows", "sha256", "source"])
        for raw in sorted((ROOT / "data" / "raw").glob("*.csv")):
            rows = len(pd.read_csv(raw, sep=";", skiprows=[1]))
            w.writerow([raw.relative_to(ROOT).as_posix(), rows, sha256(raw),
                        f"https://data.mos.ru/opendata/{raw.name.split('-')[1]}"])
        for p in out:
            w.writerow([p.relative_to(ROOT).as_posix(), len(pd.read_csv(p, sep=";")),
                        sha256(p), f"split_batches.py из {RAW.name}"])

    for p in out:
        print(f"{p.relative_to(ROOT).as_posix():45s} {len(pd.read_csv(p, sep=';')):5d}")


if __name__ == "__main__":
    main()
