# diagram-renderer

CLI-утилита для построения и актуализации диаграмм связей между markdown-файлами. В первой версии генерирует файлы [Obsidian Canvas](https://obsidian.md/) (`.canvas`).

## Возможности

- Сбор markdown-файлов по glob-паттернам.
- Извлечение связей из YAML frontmatter (wiki-ссылки вида `[[path|alias]]`).
- Построение графа зависимостей и слоистая раскладка на чистом Python.
- Запись результата в формат Obsidian Canvas.
- **Актуализация** существующей диаграммы: ручные перемещения узлов не сбрасываются, обновляются только изменившиеся узлы и рёбра.
- Пакетная обработка нескольких задач через YAML-конфиг.
- Кэширование на основе хэша набора файлов и per-node content hash.

## Установка

Инструкции по установке, требованиям и проверке окружения — в [`docs/installation.md`](docs/installation.md).

## Быстрый старт

Самый простой способ познакомиться с утилитой — запустить демо:

```bash
cd demo
PYTHONPATH=.. ../.venv/bin/python -m diagram_renderer render --config diagrams.yaml
```

Результат: `demo/skills-map.canvas`.

## Использование

- Подробнее о команде `render` — в [`docs/render.md`](docs/render.md).
- Подробнее о команде `scan` — в [`docs/scan.md`](docs/scan.md).
- Общий обзор CLI и дополнительные примеры — в [`docs/usage.md`](docs/usage.md).

## Конфигурация

Детальное описание формата конфига, полей и примеры — в [`docs/configuration.md`](docs/configuration.md).

## Разработка

### Запуск тестов

```bash
make test
```

### Покрытие

```bash
make coverage
```

## Структура проекта

```
diagram_renderer/          # исходный код CLI
  __main__.py              # точка входа
  cli/                     # argparse
  command/                 # бизнес-логика
  functions/               # чистые хелперы
  service/                 # сервисы, по одной директории на этап пайплайна
    graph.py                 # общие модели данных (Node, Edge, RenderTask, ...)
    config/                   # Config Loader
    source_collector/         # Source Collector
    link_filters/              # Link Filter (pluggable: base.py + реализации + factory.py)
    metadata_extractor/        # Metadata Extractor
    link_resolver/              # Link Resolver
    graph_builder/               # Graph Builder
    diff/                         # Diff Engine
    layout/                        # Layout Engine (pluggable: base.py + реализации + factory.py)
    writers/                        # Format Writer (pluggable: base.py + реализации + factory.py)
    cache/                          # Cache Manager
    orchestrator/                    # Orchestrator, связывает все этапы
tests/                     # тесты
docs/                      # документация
demo/                      # демонстрационный проект
```

Каждый pluggable-этап (`link_filters/`, `layout/`, `writers/`) содержит `base.py` с интерфейсом, один файл на реализацию и `factory.py`, который выбирает реализацию по значению из конфига (например, `layout.engine: layered` или `layout.engine: igraph_sugiyama`).

## Лицензия

MIT
