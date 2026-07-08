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

### Требования

- Python 3.10+
- Git (pip устанавливает пакет прямо из репозитория)

### Установка из GitHub

```bash
pip install git+https://github.com/InsonusK/ai-skill-graph-draw.git
```

После установки команда `diagram-renderer` доступна в окружении:

```bash
diagram-renderer --help
```

### Использование в другом проекте

Добавьте в `requirements.txt` строку:

```txt
diagram-renderer @ git+https://github.com/InsonusK/ai-skill-graph-draw.git
```

Чтобы привязаться к конкретной версии, укажите тег или ветку:

```txt
diagram-renderer @ git+https://github.com/InsonusK/ai-skill-graph-draw.git@v0.1.0
```

### Установка для разработки

```bash
git clone git@github.com:InsonusK/ai-skill-graph-draw.git
cd ai-skill-graph-draw
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### Проверка установки

```bash
diagram-renderer --help
# или без установки пакета
.venv/bin/python -m diagram_renderer --help
```

## Быстрый старт

Самый простой способ познакомиться с утилитой — запустить демо:

```bash
cd demo
PYTHONPATH=.. ../.venv/bin/python -m diagram_renderer render --config diagrams.yaml
```

Результат: `demo/skills-map.canvas`.

## Использование

### Через YAML-конфиг

```bash
diagram-renderer render --config diagrams.yaml [--task-id <id>] [--force]
```

### Разовая задача через CLI-аргументы

```bash
diagram-renderer render \
  --include "skills/**/*.skill.md" \
  --link-field depends_on \
  --output "skills-map.canvas"
```

Подробнее о CLI см. [`docs/usage.md`](docs/usage.md).

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
