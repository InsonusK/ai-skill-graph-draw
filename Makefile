init:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

ai-skill-sync:
	.venv/bin/python3 aism sync

test:
	.venv/bin/python -m pytest tests/ -v

coverage:
	.venv/bin/python -m coverage run -m pytest tests/ -q
	.venv/bin/python -m coverage report -m

diagram-renderer:
	.venv/bin/python -m diagram_renderer

demo-render:
	cd demo && PYTHONPATH=.. ../.venv/bin/python -m diagram_renderer render --config diagrams.yaml

demo-render-force:
	cd demo && PYTHONPATH=.. ../.venv/bin/python -m diagram_renderer render --config diagrams.yaml --force
