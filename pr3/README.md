# Практическая работа 3

Из корня репозитория:

```console
python pr3/train.py
python pr3/prepare.py pr3/data/initial.csv pr3/features.csv
python pr3/prepare.py data/incoming/batch_01.csv pr3/batch_features.csv --history pr3/data/initial.csv
```

Подготовка новой порции во второй команде с `--history` демонстрирует построение признаков; качество на новых порциях в ПР3 не оценивается.
Результаты сохранены в `pr3/reports/`, модель и её описание — в `pr3/models/`.
`pr3/data/initial.csv` побайтово совпадает с `data/initial/passenger_flow_initial.csv`.
Исходные train.py и prepare.py перенесены без изменений. Пути считаются от каталога скрипта.
Сравнение моделей повторно записывает результаты, в том числе время выполнения и дату модели. Перед повторным запуском можно проверить исходное состояние командой `git status`.
