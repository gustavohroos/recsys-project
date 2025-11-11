run-front:
	@cd recsys-front && npm i && npm run dev

.PHONY: setup
setup:
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r api/requirements.txt

.PHONY: run-api
run-api: setup
	source .venv/bin/activate && uvicorn api.main:app --reload

.PHONY: create-db
create-db: setup
	source .venv/bin/activate && python data/create_db.py