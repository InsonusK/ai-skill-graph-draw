# Команда `render`

```bash
diagram-renderer render [OPTIONS]
```

Рендерит или обновляет файл Obsidian Canvas (`.canvas`) на основе связей между markdown-файлами.

## Общие опции

| Опция | Описание |
|-------|----------|
| `--config PATH` | Путь к YAML-конфигу с задачами. |
| `--task-id ID` | Выполнить только задачу(и) с указанным id. Можно указывать несколько раз. |
| `--force` | Игнорировать кэш и полностью пересчитать диаграмму. |
| `--cache-dir PATH` | Директория для кэша. По умолчанию `.cache/diagram-renderer`. |

## Опции для разовой задачи

Если `--config` не указан, можно задать задачу прямо в командной строке:

| Опция | Описание |
|-------|----------|
| `--include PATTERN` | Glob-паттерн для исходных файлов. Можно повторять. |
| `--exclude PATTERN` | Glob-паттерн исключения. Можно повторять. |
| `--link-field NAME` | Имя поля frontmatter со ссылками. По умолчанию `depends_on`. |
| `--subpath VALUE` | Анкор для ссылок в Canvas (опционально). |
| `--on-unresolved {skip,stub}` | Поведение для внешних ссылок. По умолчанию `skip`. |
| `--layout-engine NAME` | Движок раскладки. По умолчанию `igraph_sugiyama`. |
| `--layout-direction DIR` | Направление: `LR`, `RL`, `TB`, `BT`. По умолчанию `LR`. |
| `--output-format FORMAT` | Формат вывода. По умолчанию `obsidian_canvas`. |
| `--output PATH` | Путь к выходному файлу. |
| `--edge-color VALUE` | Цвет рёбер. |
| `--edge-label VALUE` | Подпись рёбер. |
| `--transitive-reduction` | Скрыть рёбра, выводимые из более длинного пути. |

## Примеры

### Пакет задач через конфиг

```bash
diagram-renderer render --config diagrams.yaml
```

### Только одна задача из конфига

```bash
diagram-renderer render --config diagrams.yaml --task-id dotnet-solutions
```

### Принудительный пересчёт

```bash
diagram-renderer render --config diagrams.yaml --force
```

### Разовая задача

```bash
diagram-renderer render \
  --include "skills/**/*.skill.md" \
  --link-field depends_on \
  --output "skills-map.canvas"
```

### С дебаг-логами

```bash
diagram-renderer --debug render --config diagrams.yaml
```

## Коды возврата

| Код | Значение |
|-----|----------|
| `0` | Успех (возможно, часть задач пропущена по кэшу). |
| `1` | Одна или несколько задач завершились с ошибкой. |
| `2` | Ошибка валидации аргументов командной строки. |
