# Конфигурация diagram-renderer

Конфигурация описывает одну или несколько **задач** (tasks). Каждая задача — это независимая диаграмма со своим набором файлов, фильтрами связей, раскладкой и файлом результата.

## Содержание

- [Минимальный пример](#минимальный-пример)
- [Корневые поля](#корневые-поля)
- [Task](#task)
  - [source](#source)
  - [metadata](#metadata)
  - [links](#links)
  - [layout](#layout)
  - [output](#output)
- [Примеры](#примеры)
  - [Subpath в Canvas](#subpath-в-canvas)
  - [Несколько фильтров на одной диаграмме](#несколько-фильтров-на-одной-диаграмме)
  - [Несколько задач в одном конфиге](#несколько-задач-в-одном-конфиге)
- [Как писать wiki-ссылки во frontmatter](#как-писать-wiki-ссылки-во-frontmatter)

## Минимальный пример

```yaml
cache_dir: .cache/diagram-renderer

tasks:
  - id: skills-depends-on
    source:
      include:
        - "skills/**/*.skill.md"
    links:
      - name: depends_on
        type: frontmatter_field
        field: depends_on
    output:
      format: obsidian_canvas
      destination: "skills-map.canvas"
```

## Корневые поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `cache_dir` | string | Нет | Директория для кэша задач. По умолчанию `.cache/diagram-renderer`. |
| `tasks` | list[Task] | Да | Список задач на отрисовку. |

## Task

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | string | Да | Уникальный идентификатор задачи. Используется в имени файла кэша и для `--task-id`. |
| `source` | object | Да | Настройки выбора исходных markdown-файлов. |
| `metadata` | object | Нет | Настройки извлечения метаданных узла. |
| `links` | list[LinkFilter] | Да | Фильтры для поиска связей между файлами. |
| `layout` | object | Нет | Настройки раскладки. |
| `output` | object | Да | Настройки выходного файла. |

### source

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `include` | list[string] | Да | Список glob-паттернов относительно корня репозитория. Собираются только файлы, удовлетворяющие `is_file()`. |
| `exclude` | list[string] | Нет | Список glob-паттернов для исключения файлов. |

Паттерны задаются относительно текущей рабочей директории (обычно корня репозитория). Примеры:

```yaml
source:
  include:
    - "skills/**/*.skill.md"
    - "docs/**/*.md"
  exclude:
    - "**/draft/**"
    - "**/archive/*.md"
```

### metadata

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `subpath` | string | Нет | Опциональный анкор, добавляемый к ссылке узла в Canvas. Например: `#Capabilities`. Одинаков для всех узлов задачи. |

```yaml
metadata:
  subpath: "#Capabilities"
```

### links

Список фильтров связей. В одной задаче может быть несколько фильтров с разными стилями рёбер.

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `name` | string | Да | Имя фильтра, уникальное в рамках задачи. |
| `type` | string | Да | Тип фильтра. В v1 поддерживается только `frontmatter_field`. |
| `field` | string | Да | Имя поля frontmatter, из которого извлекаются ссылки. |
| `on_unresolved` | string | Нет | Поведение при ссылке на файл вне `source.include`: `skip` (по умолчанию) или `stub`. Физически несуществующие файлы всегда пропускаются с предупреждением. |
| `style` | object | Нет | Визуальный стиль рёбер фильтра. |
| `transitive_reduction` | bool | Нет | Скрывать рёбра, которые следуют из более длинного пути между теми же узлами. По умолчанию `false`. |

#### style

| Поле | Тип | Описание |
|------|-----|----------|
| `color` | string | Цвет ребра в Canvas (например, Obsidian-индекс `"4"`). |
| `label` | string | Подпись ребра. |

```yaml
links:
  - name: depends_on
    type: frontmatter_field
    field: depends_on
    on_unresolved: skip
    style:
      color: "4"
      label: "depends on"
  - name: extends
    type: frontmatter_field
    field: extends
    style:
      color: "2"
      label: "extends"
```

#### transitive_reduction

Если `A depends_on B`, `B depends_on C` и **при этом** `A depends_on C`, то ребро `A -> C` избыточно — оно следует из цепочки `A -> B -> C`. При `transitive_reduction: true` такие рёбра не попадают на диаграмму, что убирает визуальный шум в плотных графах зависимостей.

Редукция считается отдельно для каждого фильтра: цепочка, собранная из рёбер `depends_on`, не может быть использована, чтобы скрыть ребро `extends`, — это разные по смыслу связи.

```yaml
links:
  - name: depends_on
    type: frontmatter_field
    field: depends_on
    transitive_reduction: true
    style:
      color: "4"
      label: "depends on"
```

### layout

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `engine` | string | Нет | Движок раскладки: `igraph_sugiyama` (по умолчанию) или `layered`. |
| `direction` | string | Нет | `LR` (по умолчанию), `RL`, `TB`, `BT`. Принимается обоими движками, но пока не влияет на расчёт координат — расположение слоёв всегда идёт слева направо. `fromSide`/`toSide` в Canvas не зависят от этого поля: они вычисляются по фактическому взаимному расположению узлов (см. ниже). |

#### Движки раскладки

| Движок | Описание |
|--------|----------|
| `igraph_sugiyama` | По умолчанию. Слоистая/Sugiyama-раскладка, расчёт делегирован `python-igraph` (`Graph.layout_sugiyama()`) — качественная минимизация пересечений рёбер за счёт проверенной реализации. Требует пакет `python-igraph` (уже есть в `requirements.txt`; ставится как обычный wheel, без системных бинарников вроде Graphviz `dot`). |
| `layered` | Слоистая раскладка, реализованная вручную на чистом Python (barycenter-эвристика для минимизации пересечений). Без внешних зависимостей. |

Оба движка соблюдают один контракт: уже зафиксированные позиции (`fixed_positions` — узлы, которые не изменились с прошлого рендера или были вручную передвинуты в Obsidian) никогда не пересчитываются, новые узлы размещаются рядом со своими соседями.

```yaml
layout:
  engine: layered
  direction: LR
```

### output

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `format` | string | Да | Формат вывода. В v1 только `obsidian_canvas`. |
| `destination` | string | Да | Путь к выходному файлу относительно корня репозитория. |

```yaml
output:
  format: obsidian_canvas
  destination: "skills-map.canvas"
```

Сторона подключения ребра (`fromSide`/`toSide` в Canvas) вычисляется отдельно для каждого ребра по фактическим координатам узлов, а не берётся из `layout.direction`: берутся центры `fromNode` и `toNode`, доминирующая ось разницы координат (X или Y) определяет сторону — `right`/`left` при доминировании X, `bottom`/`top` при доминировании Y (координата (0, 0) канваса — левый верхний угол, Y растёт вниз).

## Примеры

### Subpath в Canvas

```yaml
tasks:
  - id: skills-with-subpath
    source:
      include:
        - "skills/**/*.skill.md"
    metadata:
      subpath: "#Capabilities"
    links:
      - name: depends_on
        type: frontmatter_field
        field: depends_on
        style:
          color: "4"
          label: "depends on"
    layout:
      engine: layered
      direction: LR
    output:
      format: obsidian_canvas
      destination: "skills-map.canvas"
```

В сгенерированном Canvas каждый узел будет содержать поле `subpath: "#Capabilities"`, и при открытии в Obsidian файл откроется сразу на соответствующем заголовке.

### Несколько фильтров на одной диаграмме

```yaml
tasks:
  - id: skills-multi-links
    source:
      include:
        - "skills/**/*.skill.md"
    links:
      - name: depends_on
        type: frontmatter_field
        field: depends_on
        style:
          color: "4"
          label: "depends on"
      - name: extends
        type: frontmatter_field
        field: extends
        style:
          color: "2"
          label: "extends"
    layout:
      engine: layered
      direction: LR
    output:
      format: obsidian_canvas
      destination: "skills-multi-links.canvas"
```

### Несколько задач в одном конфиге

```yaml
cache_dir: .cache/diagram-renderer

tasks:
  - id: dotnet-solutions
    source:
      include:
        - "skills/dotnet/**/*.skill.md"
    links:
      - name: depends_on
        type: frontmatter_field
        field: depends_on
    output:
      format: obsidian_canvas
      destination: "dotnet-map.canvas"

  - id: python-solutions
    source:
      include:
        - "skills/python/**/*.skill.md"
    links:
      - name: depends_on
        type: frontmatter_field
        field: depends_on
    output:
      format: obsidian_canvas
      destination: "python-map.canvas"
```

Запуск только одной задачи:

```bash
diagram-renderer render --config diagrams.yaml --task-id dotnet-solutions
```

## Как писать wiki-ссылки во frontmatter

YAML интерпретирует неэкранированные `[[...]]` как вложенные списки. Утилита понимает оба варианта, но рекомендуется заключать ссылки в кавычки для явности:

```yaml
# Рекомендуется
depends_on:
  - "[[skills/other.skill.md]]"
  - "[[skills/another.skill.md|Alias]]"

# Тоже работает, но менее явно
depends_on:
  - [[skills/other.skill.md]]
  - [[skills/another.skill.md|Alias]]
```

Целевой путь в ссылке должен быть относительным к корню репозитория (текущей рабочей директории).
