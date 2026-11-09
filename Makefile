.PHONY: build run stop logs test health

build:
	docker compose build

run:
	docker compose up -d --wait

stop:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm --no-deps -v "$(CURDIR)/tests:/app/tests:ro" taskboard python -m unittest discover -s tests -v

health:
	docker compose exec -T taskboard python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
