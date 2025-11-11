run-front:
	@cd recsys-front && npm i && npm run dev

.PHONY: setup
setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r api/requirements.txt

.PHONY: run-api
run-api: setup
	. .venv/bin/activate && uvicorn api.main:app --reload