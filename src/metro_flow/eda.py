"""Разведочный анализ исходной части данных (I кв. 2021 — II кв. 2024).

Запуск: python -m metro_flow.eda  (из каталога src) или python src/metro_flow/eda.py
Результат: reports/eda_stats.json и рисунки в reports/figures.
"""
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
QUARTER = {"I квартал": 1, "II квартал": 2, "III квартал": 3, "IV квартал": 4}
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 12
BLUE, ORANGE, RED, LIGHT = "#2E6DB4", "#F28E2B", "#D62728", "#A9C8EA"
R = {}


def norm(s):
    s = str(s).lower().replace("ё", "е")
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", s)).strip()


def read_mos(path):
    df = pd.read_csv(path, sep=";", skiprows=[1], encoding="utf-8")
    return df.loc[:, ~df.columns.str.startswith("Unnamed")]


def load_flow(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8")
    df = df.rename(columns={"Metro station name": "station", "Line name": "line",
                            "Incoming passengers": "inc", "Outgoing passengers": "out"})
    df["q"] = df["Quarter"].map(QUARTER)
    df["t"] = df["Year"] * 10 + df["q"]
    df["idx"] = (df["Year"] - 2021) * 4 + df["q"] - 1      # порядковый номер квартала
    df["key"] = df["station"].map(norm) + "|" + df["line"].map(norm)
    return df


d = load_flow(ROOT / "data" / "initial" / "passenger_flow_initial.csv")

# ---------------- структура ----------------
R["rows"] = len(d)
R["pairs"] = int(d["key"].nunique())
R["stations"] = int(d["station"].nunique())
R["lines"] = int(d["line"].nunique())
R["quarters"] = int(d["t"].nunique())
R["pairs_per_quarter"] = d.groupby("t").size().astype(int).to_dict()

# ---------------- качество ----------------
R["na"] = int(d.isna().sum().sum())
R["dup_key"] = int(d.duplicated(["station", "line", "Year", "Quarter"]).sum())
R["dup_gid"] = int(d["global_id"].duplicated().sum())
R["negative"] = int(((d["inc"] < 0) | (d["out"] < 0)).sum())
zero = d[(d["inc"] == 0) | (d["out"] == 0)]
R["zero_rows"] = len(zero)
R["zero_both"] = int(((d["inc"] == 0) & (d["out"] == 0)).sum())
zcnt = zero.groupby(["station", "line"]).size()
R["zero_always"] = [f"{s} ({l})" for (s, l), n in zcnt.items()
                    if n == d[(d.station == s) & (d.line == l)].shape[0]]
R["zero_pairs"] = int(len(zcnt))
R["single_rows"] = d.groupby("line").size().loc[lambda x: x < 5].astype(int).to_dict()

nz = d[(d["inc"] > 0) & (d["out"] > 0)].copy()
nz["ratio"] = nz["inc"] / nz["out"]
R["ratio_q"] = nz["ratio"].quantile([0.01, 0.5, 0.99]).round(3).tolist()
R["ratio_bad"] = nz.loc[(nz.ratio < 0.5) | (nz.ratio > 2),
                        ["station", "line", "t", "inc", "out"]].to_dict("records")
# выбросы по станции: отклонение от медианы ряда в робастных σ
nz["med"] = nz.groupby("key")["inc"].transform("median")
nz["mad"] = nz.groupby("key")["inc"].transform(lambda x: (x - x.median()).abs().median())
nz["rz"] = 0.6745 * (nz["inc"] - nz["med"]) / nz["mad"].replace(0, np.nan)
out_rows = nz[nz["rz"].abs() > 3.5]
R["outliers_station"] = len(out_rows)
R["outliers_station_pairs"] = int(out_rows["key"].nunique())
R["outliers_station_low"] = int((out_rows["rz"] < 0).sum())
q1, q3 = d["inc"].quantile([0.25, 0.75])
R["iqr_upper"] = float(q3 + 1.5 * (q3 - q1))
R["iqr_out"] = int((d["inc"] > R["iqr_upper"]).sum())
R["iqr_out_stations"] = sorted(d.loc[d["inc"] > R["iqr_upper"], "station"].unique().tolist())

# ---------------- целевая переменная ----------------
R["inc_desc"] = d["inc"].describe().round(0).to_dict()
R["inc_skew"] = round(float(d["inc"].skew()), 2)
R["loginc_skew"] = round(float(np.log1p(nz["inc"]).skew()), 2)
R["totals_mln"] = (d.groupby("t")["inc"].sum() / 1e6).round(1).to_dict()
R["share_top10"] = round(float(
    d.groupby("station")["inc"].sum().nlargest(int(0.1 * R["stations"])).sum() / d["inc"].sum()), 3)

# ---------------- справочник и вестибюли ----------------
sp = read_mos(ROOT / "data" / "raw" / "data-1488-08-09-2026.csv")
sp["key"] = sp["Station name"].map(norm) + "|" + sp["Line name"].map(norm)
for c, n in (("MCD station", "mcd"), ("Railway station", "rail"),
             ("Aeroexpress station", "aero"), ("Exit to the railway terminal", "terminal")):
    sp[n] = sp[c].notna().astype(int)
sp["center"] = sp["Area"].str.startswith("Центральный").astype(int)
pairs = d.drop_duplicates("key")
R["sp_unmatched"] = pairs.loc[~pairs["key"].isin(sp["key"]), ["station", "line"]].apply(
    lambda r: f"{r.station} ({r.line})", axis=1).tolist()

vb = read_mos(ROOT / "data" / "raw" / "data-624-11-09-2026.csv")
vb["key"] = vb["Metro station name"].map(norm) + "|" + vb["Line name"].map(norm)
vagg = vb.groupby("key").agg(n_exits=("Name", "size"),
                             tickets=("Ticket machines amount", "sum")).reset_index()
R["vb_unmatched"] = int((~pairs["key"].isin(vb["key"])).sum())
R["vb_tickets_na"] = int(vb["Ticket machines amount"].isna().sum())

# ---------------- станционная таблица за 2023 год ----------------
y23 = d[d["Year"] == 2023].groupby("key").agg(inc=("inc", "mean"), out=("out", "mean"),
                                              n=("inc", "size"))
y23 = y23[(y23["n"] == 4) & (y23["inc"] > 0)].reset_index()
st = y23.merge(sp[["key", "mcd", "rail", "aero", "terminal", "center"]], on="key", how="left") \
        .merge(vagg, on="key", how="left")

# H1. Сезонность: доля квартала в годовом потоке станции
yr = d[d["Year"].isin([2022, 2023]) & (d["inc"] > 0)]
full = yr.groupby(["key", "Year"]).filter(lambda g: len(g) == 4)
full = full.assign(share=full["inc"] / full.groupby(["key", "Year"])["inc"].transform("sum"))
wide = full.pivot_table(index=["key", "Year"], columns="q", values="share").dropna()
fr = stats.friedmanchisquare(*[wide[c] for c in (1, 2, 3, 4)])
R["h1"] = {"n": len(wide), "median_share": wide.median().round(4).tolist(),
           "friedman": round(float(fr.statistic), 1), "p": float(fr.pvalue),
           "q3_lt_q2": round(float((wide[3] < wide[2]).mean()), 3),
           "q1_min": round(float((wide.idxmin(axis=1) == 1).mean()), 3)}

# H2. Станции с пересадкой на МЦД / ж/д направление загружены сильнее
g1 = st.loc[(st["mcd"] == 1) | (st["rail"] == 1), "inc"]
g0 = st.loc[(st["mcd"] == 0) & (st["rail"] == 0), "inc"]
mw = stats.mannwhitneyu(g1, g0, alternative="greater")
R["h2"] = {"n1": len(g1), "n0": len(g0), "med1": round(float(g1.median())),
           "med0": round(float(g0.median())), "U": float(mw.statistic), "p": float(mw.pvalue)}

# H3. Число входов/выходов вестибюлей связано с потоком
s3 = st.dropna(subset=["n_exits"])
sp3 = stats.spearmanr(s3["n_exits"], s3["inc"])
sp3t = stats.spearmanr(s3["tickets"], s3["inc"])
R["h3"] = {"n": len(s3), "rho_exits": round(float(sp3.statistic), 3), "p_exits": float(sp3.pvalue),
           "rho_tickets": round(float(sp3t.statistic), 3), "p_tickets": float(sp3t.pvalue)}

# H4. Новая станция выходит на свой уровень потока не сразу
first = d[d["inc"] > 0].groupby("key")["idx"].min()
new_keys = first[first > 0].index
ramp = []
for k in new_keys:
    s = d[(d["key"] == k) & (d["inc"] > 0)].sort_values("idx")["inc"].to_numpy()
    if len(s) >= 6:
        ramp.append(s[:6] / s[2:6].mean())
ramp = np.array(ramp)
w = stats.wilcoxon(ramp[:, 0], ramp[:, 2:6].mean(axis=1), alternative="less")
R["h4"] = {"n": len(ramp), "rel_by_q": ramp.mean(axis=0).round(3).tolist(),
           "first_q_median": round(float(np.median(ramp[:, 0])), 3), "p": float(w.pvalue)}

# H5. Доля выходов — устойчивая характеристика станции
r22 = nz[nz["Year"] == 2022].groupby("key")["ratio"].mean()
r23 = nz[nz["Year"] == 2023].groupby("key")["ratio"].mean()
both = pd.concat([r22, r23], axis=1, keys=["a", "b"]).dropna()
both = both[(both.a.between(0.5, 2)) & (both.b.between(0.5, 2))]
p5 = stats.pearsonr(both["a"], both["b"])
R["h5"] = {"n": len(both), "r": round(float(p5.statistic), 3), "p": float(p5.pvalue)}

# связь между признаками и лагами
lag = d.sort_values("idx").copy()
for k in (1, 4):
    lag[f"lag{k}"] = lag.groupby("key")["inc"].shift(k)
    lag.loc[lag.groupby("key")["idx"].diff(k) != k, f"lag{k}"] = np.nan
ok = lag[(lag["inc"] > 0) & (lag["lag1"] > 0) & (lag["lag4"] > 0)]
R["corr_lag1"] = round(float(np.corrcoef(ok["inc"], ok["lag1"])[0, 1]), 3)
R["corr_lag4"] = round(float(np.corrcoef(ok["inc"], ok["lag4"])[0, 1]), 3)
R["corr_in_out"] = round(float(np.corrcoef(nz["inc"], nz["out"])[0, 1]), 4)

cm_cols = {"inc": "Входы", "out": "Выходы", "n_exits": "Число входов\nвестибюлей",
           "tickets": "Число БПА", "mcd": "Пересадка\nна МЦД", "rail": "Ж/д\nнаправление",
           "center": "ЦАО"}
cm = st[list(cm_cols)].corr(method="spearman")
R["corr_matrix"] = cm.round(2).to_dict()

# ===================== рисунки =====================
raw = pd.read_csv(ROOT / "data" / "raw" / "data-62743-08-09-2026.csv", sep=";", skiprows=[1])
raw["t"] = raw["Year"] * 10 + raw["Quarter"].map(QUARTER)
tot = raw.groupby("t")["Incoming passengers"].sum() / 1e6
labels = [f"{str(t)[2:4]}-{t % 10}" for t in tot.index]
colors = [BLUE if t <= 20242 else ORANGE for t in tot.index]
fig, ax = plt.subplots(figsize=(10, 4.2))
bars = ax.bar(range(len(tot)), tot.values, color=colors, edgecolor="white", lw=0.6)
for i, (s, e) in enumerate([(20243, 20244), (20251, 20252), (20253, 20254), (20261, 20262)], 1):
    xs = [j for j, t in enumerate(tot.index) if s <= t <= e]
    ax.text(np.mean(xs), tot.max() * 1.03, f"batch_{i:02d}", ha="center", fontsize=10)
ax.text(6.5, tot.max() * 1.03, "исходная часть (4009 записей)", ha="center", fontsize=10)
ax.set_xticks(range(len(tot)), labels, rotation=90, fontsize=10)
ax.set_ylabel("Входы, млн пассажиров"); ax.set_xlabel("Год-квартал")
ax.set_ylim(0, tot.max() * 1.12)
fig.savefig(FIG / "fig2_1_split.png", dpi=200, bbox_inches="tight"); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
axs[0].hist(d["inc"] / 1e6, bins=40, color=BLUE, edgecolor="white", lw=0.5)
axs[0].set_xlabel("Входы за квартал, млн"); axs[0].set_ylabel("Число записей")
axs[0].set_title("а) исходная шкала", fontsize=12)
axs[1].hist(np.log10(nz["inc"]), bins=40, color=ORANGE, edgecolor="white", lw=0.5)
axs[1].set_xlabel("lg(входы за квартал)"); axs[1].set_title("б) логарифмическая шкала", fontsize=12)
fig.tight_layout(); fig.savefig(FIG / "fig2_2_target.png", dpi=200, bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 5.2))
ax.scatter(nz["out"] / 1e6, nz["inc"] / 1e6, s=6, c=BLUE, alpha=0.5)
bad = nz[(nz.ratio < 0.5) | (nz.ratio > 2)]
ax.scatter(bad["out"] / 1e6, bad["inc"] / 1e6, s=80, facecolors="none", edgecolors=RED, lw=2)
for _, r in bad.iterrows():
    ax.annotate(f"{r.station}, {str(r.t)[:4]}-{r.t % 10}", (r.out / 1e6, r.inc / 1e6),
                xytext=(8, -4), textcoords="offset points", fontsize=10, color=RED)
m = max(nz["inc"].max(), nz["out"].max()) / 1e6
ax.plot([0, m], [0, m], "k--", lw=0.8)
ax.set_xlabel("Выходы, млн"); ax.set_ylabel("Входы, млн")
fig.savefig(FIG / "fig2_3_in_out.png", dpi=200, bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4))
bp = ax.boxplot([wide[c] * 100 for c in (1, 2, 3, 4)], showfliers=False, patch_artist=True,
                medianprops=dict(color="black"))
for patch_, col in zip(bp["boxes"], ["#A9C8EA", "#8BC34A", "#F6C85F", "#F28E2B"]):
    patch_.set_facecolor(col)
ax.set_xticks([1, 2, 3, 4], ["I", "II", "III", "IV"])
ax.axhline(25, color="black", ls=":", lw=0.8)
ax.set_xlabel("Квартал"); ax.set_ylabel("Доля квартала в годовом потоке, %")
fig.savefig(FIG / "fig2_4_season.png", dpi=200, bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7.4, 6))
im = ax.imshow(cm.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(cm)), [cm_cols[c] for c in cm.columns], fontsize=10, rotation=45, ha="right")
ax.set_yticks(range(len(cm)), [cm_cols[c] for c in cm.columns], fontsize=10)
for i in range(len(cm)):
    for j in range(len(cm)):
        v = cm.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=10,
                color="white" if abs(v) > 0.7 else "black")
fig.colorbar(im, ax=ax, fraction=0.046)
fig.savefig(FIG / "fig2_5_corr.png", dpi=200, bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.8))
for row in ramp:
    ax.plot(range(1, 7), row, color=LIGHT, lw=0.8)
ax.plot(range(1, 7), ramp.mean(axis=0), color=RED, lw=2.4, marker="o", label="среднее")
ax.axhline(1, color="black", ls=":", lw=0.8)
ax.set_xlabel("Номер квартала с момента открытия")
ax.set_ylabel("Поток / средний поток\nкварталов 3–6")
ax.legend(); ax.set_ylim(0, 2)
fig.savefig(FIG / "fig2_6_ramp.png", dpi=200, bbox_inches="tight"); plt.close(fig)

(ROOT / "reports" / "eda_stats.json").write_text(
    json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
