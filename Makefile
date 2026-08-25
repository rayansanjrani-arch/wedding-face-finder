.PHONY: install install-dev test lint format audit clean run docker-build docker-up

# Python
PYTHON := python3
PIP := pip3

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=wedding_face_finder --cov-report=term-missing

lint:
	black --check .
	flake8 wedding_face_finder/ tests/
	mypy wedding_face_finder/
	bandit -r wedding_face_finder/

format:
	black .

audit:
	pip-audit --requirement requirements.txt
	pip-audit --requirement requirements-dev.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ .coverage

run:
	python run.py

docker-build:
	docker build -t wedding-face-finder:latest .

docker-up:
	docker-compose up --build -d
