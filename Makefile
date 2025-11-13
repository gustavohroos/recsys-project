run-front:
	@cd recsys-front && npm i && npm run dev

.PHONY: setup
setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r api/requirements.txt

.PHONY: run-api
run-api: setup
	. .venv/bin/activate && uvicorn api.main:app --reload
	. .venv/bin/activate && uvicorn api.main:app --reload

.PHONY: create-db
create-db: setup
	. .venv/bin/activate && python data/create_db.py

.PHONY: generate-recommendations
generate-recommendations: setup
	. .venv/bin/activate && python recsys/generate_recommendations.py --models random item_similarity --top-n 5 --seed 42