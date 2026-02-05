format:
	poetry run black .

test:
	poetry run pytest tests/ -v --cache-clear

run:
	poetry run uvicorn app.main:app --port 8080 --reload

install:
	poetry install
	poetry run alembic upgrade head
	poetry run python3 initial_data.py
