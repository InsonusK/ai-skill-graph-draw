init:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

ai-skill-sync:
	.venv/bin/python3 aism sync