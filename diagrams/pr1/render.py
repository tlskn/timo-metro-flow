"""Схемы для отчёта по ПР1: жизненный цикл, архитектура, структура репозитория."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 12


def box(ax, x, y, w, h, text, fill="#ffffff", bold=False, fs=12):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fill, ec="black", lw=1.2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, p, q, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14,
                                 lw=1.2, color="black", linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))


# --- Рисунок 1.1: жизненный цикл ---
fig, ax = plt.subplots(figsize=(10, 6.4))
ax.set_xlim(0, 10); ax.set_ylim(0, 6.4); ax.axis("off")
stages = [
    (1.7, 5.4, "1. Бизнес-постановка\nцель: планирование\nнагрузки на станции"),
    (5.0, 5.4, "2. Получение данных\ndata.mos.ru, раз в квартал\n(3 набора, CSV)"),
    (8.3, 5.4, "3. Проверка и подготовка\nсхема данных, сопоставление\nстанций, признаки"),
    (8.3, 3.2, "4. Обучение и валидация\nскользящее окно\nпо кварталам"),
    (8.3, 1.0, "5. Пакетный расчёт\nпрогноз, аномалии,\nкластеры → витрина"),
    (5.0, 1.0, "6. Дашборд\nдля пользователя\n(Streamlit)"),
    (1.7, 1.0, "7. Мониторинг\nошибка на новом квартале,\nдрейф признаков"),
    (1.7, 3.2, "8. Решение\nо переобучении"),
]
for x, y, t in stages:
    box(ax, x, y, 2.9, 1.25, t, fill="#f2f2f2" if t.startswith(("1", "8")) else "#ffffff")
arrow(ax, (3.15, 5.4), (3.55, 5.4)); arrow(ax, (6.45, 5.4), (6.85, 5.4))
arrow(ax, (8.3, 4.77), (8.3, 3.83)); arrow(ax, (8.3, 2.57), (8.3, 1.63))
arrow(ax, (6.85, 1.0), (6.45, 1.0)); arrow(ax, (3.55, 1.0), (3.15, 1.0))
arrow(ax, (1.7, 1.63), (1.7, 2.57))
arrow(ax, (3.15, 3.2), (6.85, 3.2), ls="--")
ax.text(5.0, 3.42, "новый квартал данных / рост ошибки", ha="center", fontsize=11, style="italic")
arrow(ax, (1.7, 3.83), (1.7, 4.77), ls="--")
ax.text(1.85, 4.3, "пересмотр\nпостановки", ha="left", va="center", fontsize=10, style="italic")
fig.savefig("img/fig1_1_lifecycle.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# --- Рисунок 1.2: архитектура ---
fig, ax = plt.subplots(figsize=(10, 7.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 7.6); ax.axis("off")
# источники
for x, t in [(1.7, "Пассажиропоток\nпо станциям\n(набор 62743)"),
             (5.0, "Входы и выходы\nвестибюлей\n(набор 624)"),
             (8.3, "Справочник\nстанций\n(набор 1488)")]:
    box(ax, x, 6.95, 2.6, 0.95, t, fill="#f2f2f2")
box(ax, 5.0, 5.55, 8.6, 0.7, "data/raw — исходные CSV под контролем DVC (хэш-версия каждой выгрузки)")
for x in (1.7, 5.0, 8.3):
    arrow(ax, (x, 6.47), (x, 5.9))
box(ax, 5.0, 4.5, 8.6, 0.8, "Проверка качества (pandera) → очистка, приведение названий станций,\nобъединение по ключу «станция + линия» → data/processed")
arrow(ax, (5.0, 5.2), (5.0, 4.9))
box(ax, 5.0, 3.45, 8.6, 0.7, "Построение признаков: лаги, сезонность, доля выходов, число вестибюлей, округ, пересадки")
arrow(ax, (5.0, 4.1), (5.0, 3.8))
for x, t in [(1.7, "Прогноз потока\nна 1–4 квартала\n(CatBoost, SARIMA)"),
             (5.0, "Поиск аномалий\n(остатки прогноза,\nIsolation Forest)"),
             (8.3, "Кластеризация\nстанций\n(k-means, иерарх.)")]:
    box(ax, x, 2.25, 2.6, 1.0, t)
    arrow(ax, (x, 3.1), (x, 2.75))
box(ax, 5.6, 0.9, 4.6, 0.75, "Витрина результатов (Parquet)\n+ дашборд Streamlit", fill="#f2f2f2", bold=True)
for x in (1.7, 5.0, 8.3):
    arrow(ax, (x + (0.5 if x < 5 else 0), 1.75), (5.6 + (x - 5.0) * 0.4, 1.28))
box(ax, 1.4, 0.9, 2.2, 0.75, "MLflow: метрики,\nверсии моделей", fs=11)
arrow(ax, (1.2, 1.75), (1.2, 1.28), ls="--")
fig.savefig("img/fig1_2_architecture.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# --- Рисунок 1.3: структура репозитория ---
tree = """metro-flow/
├── data/
│   ├── raw/            исходные CSV с data.mos.ru (*.dvc)
│   ├── interim/        данные после очистки
│   └── processed/      объединённая таблица и признаки
├── notebooks/          EDA и эксперименты (01_eda.ipynb, ...)
├── src/metro_flow/
│   ├── data/           загрузка, проверка схемы, очистка
│   ├── features/       построение признаков
│   ├── models/         forecast.py, anomalies.py, clustering.py
│   └── app/            дашборд Streamlit
├── tests/              тесты pytest
├── models/             сохранённые модели (под DVC)
├── reports/            рисунки и таблицы для отчётов
├── dvc.yaml            описание стадий пайплайна
├── params.yaml         гиперпараметры и границы выборок
├── pyproject.toml      зависимости проекта
├── uv.lock             зафиксированные версии пакетов
└── Dockerfile          образ для запуска на любой машине"""
fig, ax = plt.subplots(figsize=(9, 5.6))
ax.axis("off")
ax.text(0.01, 0.99, tree, ha="left", va="top", family="Consolas", fontsize=11.5,
        transform=ax.transAxes)
fig.savefig("img/fig1_3_repo.png", dpi=200, bbox_inches="tight"); plt.close(fig)
print("ok")
