"""Диаграммы для отчёта по ПР2: C4 (контекст, контейнеры), UML (варианты
использования, последовательность, деятельность)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 12
OUT = "img/"
PERSON, SYSTEM, CONT, EXT, STORE, LIGHT, ORANGE = (
    "#08427B", "#1168BD", "#438DD5", "#8C8C8C", "#2E8B57", "#DCEAF7", "#FCE3C6")


def box(ax, x, y, w, h, text, fill=LIGHT, fs=11, rounded=True, ls="-", lw=1.2, tc=None):
    style = "round,pad=0.02,rounding_size=0.08" if rounded else "square,pad=0.0"
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style,
                                fc=fill, ec="#1F3A5F", lw=lw, linestyle=ls))
    if tc is None:
        tc = "white" if fill in (PERSON, SYSTEM, CONT, EXT, STORE) else "black"
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc)


def arrow(ax, p, q, text="", ls="-", off=(0, 0), fs=10, rad=0.0, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, lw=1.1,
                                 color="black", linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text,
                ha="center", va="center", fontsize=fs, style="italic",
                bbox=dict(fc="white", ec="none", pad=0.6))


def person(ax, x, y, text, fs=11):
    ax.add_patch(plt.Circle((x, y + 0.42), 0.17, fc=PERSON, ec=PERSON, lw=1.1))
    ax.plot([x, x], [y + 0.25, y - 0.15], color=PERSON, lw=1.6)
    ax.plot([x - 0.25, x + 0.25], [y + 0.12, y + 0.12], color=PERSON, lw=1.6)
    ax.plot([x, x - 0.2], [y - 0.15, y - 0.45], color=PERSON, lw=1.6)
    ax.plot([x, x + 0.2], [y - 0.15, y - 0.45], color=PERSON, lw=1.6)
    ax.text(x, y - 0.62, text, ha="center", va="top", fontsize=fs)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(OUT + name, dpi=200, bbox_inches="tight"); plt.close(fig)


# ---------------- Рисунок 2.7: C4, уровень контекста ----------------
fig, ax = canvas(11, 6.2)
person(ax, 1.1, 4.3, "Планировщик\n[служба планирования\nдвижения]")
person(ax, 9.9, 4.3, "Аналитик данных\n[сопровождает\nсистему]")
box(ax, 5.5, 4.3, 3.6, 1.6, "Система анализа\nпассажиропотока\n[программная система]\nпрогноз, аномалии, кластеры,\nключевые показатели",
    fill=SYSTEM, fs=11)
box(ax, 2.2, 0.9, 3.2, 1.1, "Портал открытых данных\ndata.mos.ru\n[внешняя система]", fill=EXT)
box(ax, 8.8, 0.9, 3.2, 1.1, "Внутренние системы\nметрополитена\n[внешняя система]", fill=EXT, ls="--")
arrow(ax, (1.55, 4.45), (3.7, 4.45), "смотрит показатели,\nпрогноз, аномалии", off=(0, 0.5))
arrow(ax, (9.45, 4.45), (7.3, 4.45), "загружает порции,\nпереобучает модели", off=(0, 0.5))
arrow(ax, (2.6, 1.45), (4.4, 3.5), "квартальные CSV\n(3 набора)", off=(-1.0, 0.1))
arrow(ax, (8.4, 1.45), (6.6, 3.5), "прогноз по запросу\n[REST, JSON]", off=(1.0, 0.1), ls="--", style="<|-")
save(fig, "fig2_7_c4_context.png")

# ---------------- Рисунок 2.8: C4, уровень контейнеров ----------------
fig, ax = canvas(14.5, 9.6)
c1, c2, c3, c4 = 2.9, 6.2, 9.5, 12.8
r1, r2, r3 = 6.3, 4.2, 2.1
ax.add_patch(Rectangle((1.25, 1.2), 13.1, 6.1, fc="none", ec="black", lw=1.1, ls="--"))
ax.text(14.2, 7.15, "Система анализа пассажиропотока [граница системы]", fontsize=10.5,
        style="italic", va="top", ha="right")
box(ax, c1, 8.7, 3.0, 0.8, "data.mos.ru\n[внешняя система]", fill=EXT, fs=10)
person(ax, 0.55, 6.5, "Аналитик", fs=10.5)
person(ax, 0.55, 2.3, "Планировщик", fs=10.5)
box(ax, c4, 0.2, 3.0, 0.8, "Внутренние системы\n[внешняя система]", fill=EXT, fs=10, ls="--")
C = dict(fs=10, fill=CONT)
box(ax, c1, r1, 2.9, 1.0, "Загрузчик порций\n[Python, стадия DVC]\nчтение, приведение типов", **C)
box(ax, c2, r1, 2.9, 1.0, "Проверка качества\n[Python, pandera]\nтребования D-01…D-08", **C)
box(ax, c3, r1, 2.9, 1.0, "Пайплайн признаков\n[Python, pandas]\nочистка, обогащение", **C)
box(ax, c4, r1, 2.9, 1.0, "ML-модуль\n[CatBoost, scikit-learn]\nпрогноз, аномалии, кластеры", **C)
box(ax, (c1 + c2) / 2, r2, 5.8, 0.9, "Хранилище данных [CSV, Parquet + DVC]\ndata/raw, data/incoming, data/processed, отчёты проверки",
    **{**C, "fill": STORE})
box(ax, c3, r2, 2.9, 0.9, "Расчёт показателей\n[Python] K-01…K-05", **C)
box(ax, c4, r2, 2.9, 0.9, "MLflow\n[трекинг, реестр моделей]", **{**C, "fill": STORE})
box(ax, c2, r3, 2.9, 0.9, "Панель\n[Streamlit, Plotly]", **C)
box(ax, c3, r3, 2.9, 0.9, "Витрина [Parquet]\nпрогнозы, аномалии, KPI", **{**C, "fill": STORE})
box(ax, c4, r3, 2.9, 0.9, "API\n[FastAPI, REST/JSON]", **C)

arrow(ax, (c1, 8.3), (c1, r1 + 0.5), "CSV", off=(0.3, 0))
arrow(ax, (0.95, 6.5), (c1 - 1.45, r1), "запуск", off=(0, 0.25))
arrow(ax, (c1 + 1.45, r1), (c2 - 1.45, r1))
arrow(ax, (c2 + 1.45, r1), (c3 - 1.45, r1), "годная\nпорция", off=(0, -0.4))
arrow(ax, (c3 + 1.45, r1), (c4 - 1.45, r1), "признаки", off=(0, 0.3))
arrow(ax, (c1, r1 - 0.5), (c1, r2 + 0.45), "исходные\nданные", off=(-0.55, 0))
arrow(ax, (c2, r1 - 0.5), (c2, r2 + 0.45), "отчёт", off=(0.4, 0))
arrow(ax, (c3 - 0.9, r1 - 0.5), ((c1 + c2) / 2 + 2.9, r2 + 0.3), "таблица\nпризнаков", off=(0.15, 0.0))
arrow(ax, (c4, r1 - 0.5), (c4, r2 + 0.45), "метрики,\nмодели", off=(0.55, 0))
arrow(ax, (c4 - 0.9, r1 - 0.5), (c3 + 0.6, r2 + 0.45), "прогнозы", off=(0.1, 0.05))
arrow(ax, ((c1 + c2) / 2 + 2.9, r2 - 0.15), (c3 - 1.45, r2 - 0.15))
arrow(ax, (c3, r2 - 0.45), (c3, r3 + 0.45))
arrow(ax, (c3 - 1.45, r3), (c2 + 1.45, r3))
arrow(ax, (c3 + 1.45, r3), (c4 - 1.45, r3))
arrow(ax, (0.95, 2.3), (c2 - 1.45, r3), "смотрит показатели", off=(0.6, 0.25))
arrow(ax, (c4, 0.6), (c4, r3 - 0.45), "запрос прогноза", off=(-1.0, 0), ls="--")
ax.set_ylim(-0.3, 9.6)
save(fig, "fig2_8_c4_containers.png")

# ---------------- Рисунок 2.9: UML, варианты использования ----------------
fig, ax = canvas(10.5, 7.6)
ax.add_patch(Rectangle((2.6, 0.2), 5.3, 7.2, fc="#F5F9FD", ec=SYSTEM, lw=1.4))
ax.text(5.25, 7.2, "Система анализа пассажиропотока", ha="center", fontsize=11, style="italic")
person(ax, 1.1, 5.4, "Аналитик\nданных")
person(ax, 9.4, 5.4, "Планировщик")
person(ax, 9.4, 1.6, "Внутренняя\nсистема")
uc = {
    "load": (5.25, 6.5, "Загрузить порцию"),
    "check": (5.25, 5.55, "Проверить качество"),
    "retrain": (5.25, 4.6, "Переобучить модели"),
    "report": (5.25, 3.65, "Просмотреть отчёт\nо проверке"),
    "kpi": (5.25, 2.7, "Просмотреть показатели\nи их динамику"),
    "anom": (5.25, 1.75, "Разобрать список аномалий"),
    "api": (5.25, 0.8, "Получить прогноз\nпо станции"),
}
for k, (x, y, t) in uc.items():
    ax.add_patch(Ellipse((x, y), 3.3, 0.66, fc="#FFF4D6", ec="#B8860B", lw=1.2))
    ax.text(x, y, t, ha="center", va="center", fontsize=10.5)


def line(p, q, ls="-"):
    ax.plot([p[0], q[0]], [p[1], q[1]], "k", lw=1.0, ls=ls)


for k in ("load", "retrain", "report", "anom"):
    line((1.45, 5.3), (3.6, uc[k][1]))
for k in ("kpi", "anom", "api"):
    pass
line((9.05, 5.3), (6.9, uc["kpi"][1])); line((9.05, 5.3), (6.9, uc["anom"][1]))
line((9.05, 5.3), (6.9, uc["api"][1]))
line((9.05, 1.5), (6.9, uc["api"][1]))
arrow(ax, (5.25, 6.17), (5.25, 5.88), ls="--")
ax.text(5.45, 6.03, "«include»", fontsize=9, style="italic", va="center")
save(fig, "fig2_9_usecase.png")

# ---------------- Рисунок 2.10: UML, последовательность ----------------
fig, ax = canvas(11.5, 8.2)
parts = ["Аналитик", "Загрузчик", "Проверка\nкачества", "Пайплайн\nпризнаков", "ML-модуль",
         "Расчёт\nпоказателей", "Витрина"]
xs = [0.8 + i * 1.65 for i in range(len(parts))]
top = 7.7
for x, p in zip(xs, parts):
    box(ax, x, top, 1.45, 0.7, p, fs=10, rounded=False, fill=CONT if p != "Аналитик" else PERSON)
    ax.plot([x, x], [top - 0.35, 0.3], "k", lw=0.8, ls="--")
msgs = [
    (0, 1, 7.0, "load(batch_02.csv)"),
    (1, 1, 6.6, "чтение, типы", True),
    (1, 2, 6.1, "validate(df)"),
    (2, 1, 5.6, "отчёт: ошибки, флаги", False, "--"),
]
y = 7.0


def msg(i, j, y, t, ls="-"):
    ax.add_patch(FancyArrowPatch((xs[i], y), (xs[j], y), arrowstyle="-|>", mutation_scale=12,
                                 lw=1.0, color="black", linestyle=ls))
    ax.text((xs[i] + xs[j]) / 2, y + 0.1, t, ha="center", va="bottom", fontsize=9.5,
            bbox=dict(fc="white", ec="none", pad=0.4))


def self_msg(i, y, t):
    x = xs[i]
    ax.plot([x, x + 0.35, x + 0.35], [y + 0.1, y + 0.1, y - 0.15], "k", lw=1.0)
    ax.add_patch(FancyArrowPatch((x + 0.35, y - 0.15), (x, y - 0.15), arrowstyle="-|>",
                                 mutation_scale=10, lw=1.0, color="black"))
    ax.text(x + 0.42, y - 0.02, t, ha="left", va="center", fontsize=9.5,
            bbox=dict(fc="white", ec="none", pad=0.4))


msg(0, 1, 7.05, "загрузить порцию batch_XX.csv")
self_msg(1, 6.75, "чтение CSV, приведение типов")
msg(1, 2, 6.25, "проверить(таблица)")
msg(2, 1, 5.8, "отчёт о проверке", ls="--")
# alt-фрейм
ax.add_patch(Rectangle((0.15, 0.55), 11.2, 4.95, fc="#F5F9FD", ec=SYSTEM, lw=1.2, zorder=0))
ax.add_patch(Polygon([(0.15, 5.5), (1.15, 5.5), (1.15, 5.25), (1.0, 5.1), (0.15, 5.1)],
                     fc=LIGHT, ec=SYSTEM, lw=1.0))
ax.text(0.22, 5.3, "alt", fontsize=10, fontweight="bold", va="center")
ax.text(1.3, 5.3, "[доля нарушений ≤ 1 %]", fontsize=9.5, va="center", style="italic")
msg(1, 3, 4.85, "очистить и построить признаки")
self_msg(3, 4.55, "transform (параметры из обучения)")
msg(3, 4, 4.05, "таблица признаков")
self_msg(4, 3.75, "predict: прогноз, аномалии")
msg(4, 5, 3.25, "прогнозы и оценки аномалий")
self_msg(5, 2.95, "пересчёт K-01…K-05")
msg(5, 6, 2.45, "записать новую версию")
msg(6, 0, 2.0, "показатели обновлены", ls="--")
ax.plot([0.15, 11.35], [1.55, 1.55], "k", lw=0.9, ls="--")
ax.text(0.3, 1.35, "[доля нарушений > 1 %]", fontsize=9.5, va="center", style="italic")
msg(1, 0, 0.9, "порция отклонена, витрина не изменена", ls="--")
save(fig, "fig2_10_sequence.png")

# ---------------- Рисунок 2.11: UML, деятельность (пайплайн) ----------------
fig, ax = canvas(10, 11.5)
X = 4.0


def act(y, t, x=X, w=4.2, h=0.62, fill=LIGHT):
    box(ax, x, y, w, h, t, fill=fill, fs=10.5)


ax.add_patch(plt.Circle((X, 11.1), 0.16, fc="black"))
act(10.3, "Прочитать файл порции, привести типы")
act(9.35, "Проверить схему и требования D-01…D-08")
ax.add_patch(Polygon([(X, 8.65), (X + 0.35, 8.35), (X, 8.05), (X - 0.35, 8.35)], fc="white", ec="black"))
act(8.35, "Записать отчёт,\nпорцию отклонить", x=8.0, w=2.9, h=0.75, fill="#F8D0D0")
ax.add_patch(plt.Circle((8.0, 7.35), 0.16, fc="white", ec="black", lw=1.2))
ax.add_patch(plt.Circle((8.0, 7.35), 0.09, fc="black"))
act(7.45, "Исключить записи с нарушениями,\nудалить структурные нули")
act(6.5, "Нормализовать названия, присоединить\nсправочник и агрегаты вестибюлей")
ax.add_patch(Polygon([(X, 5.85), (X + 0.35, 5.55), (X, 5.25), (X - 0.35, 5.55)], fc="white", ec="black"))
act(4.6, "Оценить параметры преобразований\nи сохранить transform.json",
    x=7.6, w=3.6, h=0.75, fill=ORANGE)
act(4.6, "Загрузить сохранённые\nпараметры", x=1.2, w=2.2, h=0.75)
ax.add_patch(Polygon([(X, 3.95), (X + 0.35, 3.65), (X, 3.35), (X - 0.35, 3.65)], fc="white", ec="black"))
act(2.85, "Сформировать признаки (лаги, сезонность,\nсрок работы станции, доля выходов)")
act(1.9, "Сохранить features.parquet, зафиксировать в DVC")
ax.add_patch(plt.Circle((X, 1.05), 0.16, fc="white", ec="black", lw=1.2))
ax.add_patch(plt.Circle((X, 1.05), 0.09, fc="black"))
arrow(ax, (X, 10.94), (X, 10.61))
arrow(ax, (X, 9.99), (X, 9.66))
arrow(ax, (X, 9.04), (X, 8.65))
arrow(ax, (X + 0.35, 8.35), (6.55, 8.35), "[нарушений > 1 %]", off=(0.25, 0.25))
arrow(ax, (8.0, 7.97), (8.0, 7.51))
arrow(ax, (X, 8.05), (X, 7.83), "")
ax.text(X + 0.12, 7.9, "[иначе]", fontsize=10, style="italic", va="center")
arrow(ax, (X, 7.07), (X, 6.88))
arrow(ax, (X, 6.12), (X, 5.85))
arrow(ax, (X + 0.35, 5.55), (7.6, 4.98), "[обучение]", off=(0.6, 0.15))
arrow(ax, (X - 0.35, 5.55), (1.2, 4.98), "[новая порция]", off=(-0.75, 0.15))
arrow(ax, (7.6, 4.22), (X + 0.35, 3.65))
arrow(ax, (1.2, 4.22), (X - 0.35, 3.65))
arrow(ax, (X, 3.35), (X, 3.23))
arrow(ax, (X, 2.47), (X, 2.21))
arrow(ax, (X, 1.59), (X, 1.21))
ax.text(7.6, 4.1, "только при обучении", fontsize=10, style="italic", ha="center", va="top")
save(fig, "fig2_11_activity.png")
print("ok")
