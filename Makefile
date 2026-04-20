.PHONY: build up down migrate migrations test lint format superuser fixtures clean

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	docker-compose exec api python manage.py migrate

migrations:
	docker-compose exec api python manage.py makemigrations

test:
	docker-compose exec api pytest --cov=apps --cov-report=html

lint:
	docker-compose exec api flake8 apps/
	docker-compose exec api mypy apps/

format:
	docker-compose exec api black apps/
	docker-compose exec api isort apps/

superuser:
	docker-compose exec api python manage.py createsuperuser

fixtures:
	docker-compose exec api python manage.py loaddata fixtures/*.json

collectstatic:
	docker-compose exec api python manage.py collectstatic --noinput

shell:
	docker-compose exec api python manage.py shell

dbshell:
	docker-compose exec api python manage.py dbshell

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
