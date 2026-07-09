# Установка diagram-renderer

## Требования

- Python 3.10+
- Git (pip устанавливает пакет прямо из репозитория)

## Установка из GitHub

```bash
pip install git+https://github.com/InsonusK/ai-skill-graph-draw.git
```

После установки команда `diagram-renderer` доступна в окружении:

```bash
diagram-renderer --help
```

## Использование в другом проекте

Добавьте в `requirements.txt` строку:

```txt
diagram-renderer @ git+https://github.com/InsonusK/ai-skill-graph-draw.git
```

Чтобы привязаться к конкретной версии, укажите тег или ветку:

```txt
diagram-renderer @ git+https://github.com/InsonusK/ai-skill-graph-draw.git@v0.1.0
```

## Установка для разработки

```bash
git clone git@github.com:InsonusK/ai-skill-graph-draw.git
cd ai-skill-graph-draw
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Проверка установки

```bash
diagram-renderer --help
# или без установки пакета
.venv/bin/python -m diagram_renderer --help
```
