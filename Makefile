.deps/setup:
	@mkdir .deps
	@touch $@

.deps/requirements: .deps/setup requirements.txt
	@echo "Installing dependencies..."
	@pip install -r requirements.txt > $@

.deps/migrate: .deps/requirements $(wildcard ./**/migrations/*.py) $(wildcard ./**/models.py)
	@echo "Generating migrations..."
	@python manage.py makemigrations --settings=scrutiny.settings.local
	@echo "Migrating database..."
	@python manage.py migrate --settings=scrutiny.settings.local
	@touch $@

.deps/lint: .deps/requirements $(wildcard ./**/*.py) $(wildcard templates/**/*.html)
	@echo "Formating python files..."
	@black .
	@echo "Formating html files..."
	@djlint --reformat --quiet templates || true
	@touch $@

.deps: .deps/lint .deps/migrate
	@touch $@

build:
	@docker build -f docker/DockerfileScrutiny -t blong14/scrutiny:latest .
	@touch docker/DockerfileScrutiny

image: build
	@docker push blong14/scrutiny:latest
	@docker images --format="{{json .}}" --no-trunc blong14/scrutiny:latest > $@

build-pypy:
	@docker build -f DockerfilePyPy -t blong14/scrutiny-pypy:latest .
	@touch Dockerfile

build-python:
	@docker build -f docker/Dockerfile -t blong14/scrutiny-python:latest .
	@#docker run --rm blong14/scrutiny pypy manage.py test --timing --settings=scrutiny.settings.spec
	@touch docker/Dockerfile

.PHONY: check clean cover run seed shell test
check: .deps
	@python manage.py check --settings=scrutiny.settings.local

clean:
	@echo "Cleaning dependencies..."
	@rm -rf .deps
	@rm -f scrutiny/db.sqlite3
	@pip uninstall -r requirements.txt -y

cover:
	COVERAGE_PROCESS_START=$(PWD)/.coveragerc COVERAGE_FILE=$(PWD)/.coverage PYTHONPATH=$(PWD) pytest --durations=0
	@coverage html

cover-ci:
	COVERAGE_PROCESS_START=$(PWD)/.coveragerc COVERAGE_FILE=$(PWD)/.coverage PYTHONPATH=$(PWD) pytest --durations=0
	@coverage xml

lint-ci:
	@black .
	@djlint --quiet templates || true

run:
	@docker-compose up -d postgres
	@python manage.py runserver 0.0.0.0:8089 --settings=scrutiny.settings.local

seed: .deps
	@python manage.py seed --settings=scrutiny.settings.local

shell: .deps
	@python manage.py shell --settings=scrutiny.settings.local

test:
	@pytest --durations=0 --verbosity=1
