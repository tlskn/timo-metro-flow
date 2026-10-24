# metro-flow

Семестровый проект «Система анализа пассажиропотока Московского метрополитена».

## Данные

| Каталог | Содержимое |
|---|---|
| `data/raw/` | исходные выгрузки data.mos.ru (наборы 62743, 624, 1488), не изменяются |
| `data/initial/` | исходная часть: I кв. 2021 — II кв. 2024 |
| `data/incoming/` | порции «новых» данных `batch_01.csv` … `batch_04.csv`, по полгода |
| `data/manifest.csv` | имя файла, число строк, SHA-256, источник |

## Запуск

```
pip install -r requirements.txt
python scripts/split_batches.py     # разбиение на исходную часть и порции
python src/metro_flow/eda.py        # разведочный анализ -> reports/
```
