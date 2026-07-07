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
- Git (для установки `ai-skill-manager` из репозитория)

### Быстрая установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd ai-skill-graph-draw

# Создать виртуальное окружение и установить зависимости
make init
```

Или вручную:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Проверка установки

```bash
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
diagram_renderer/      # исходный код CLI
  __main__.py          # точка входа
  cli/                 # argparse
  command/             # бизнес-логика
  functions/           # чистые хелперы
  service/             # сервисы (graph, layout, cache, ...)
tests/                 # тесты
docs/                  # документация
demo/                  # демонстрационный проект
```

## Лицензия

MIT
