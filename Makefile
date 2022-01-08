.deps/setup:
	@mkdir .deps
	@touch $@

.deps/requirements: .deps/setup requirements.txt
	@echo "Installing dependencies..."
	@pip install -r requirements.txt > $@

.deps/migrate: .deps/requirements $(wildcard ./**/migrations/*.py) $(wildcard ./**/models.py)
	@echo "Generating migrations..."
	@python manage.py makemigrations --settings=scrutiny.settings.dev
	@echo "Migrating database..."
	@python manage.py migrate --settings=scrutiny.settings.dev
	@touch $@

.deps/lint: .deps/requirements $(wildcard ./**/*.py) $(wildcard templates/**/*.html)
	@echo "Formating python files..."
	@black .
	@echo "Formating html files..."
	@djlint --reformat --quiet templates || true
	@touch $@

.deps: .deps/lint .deps/migrate
	@touch $@

image: .deps/lint .dockerignore Dockerfile Makefile
	@docker push blong14/scrutiny:latest
	@docker images --format="{{json .}}" --no-trunc blong14/scrutiny:latest > $@

build-pypy:
	@docker build -f DockerfilePyPy -t blong14/scrutiny-pypy:latest .
	@touch Dockerfile

build-python:
	@docker build -f DockerfilePython -t blong14/scrutiny-python:latest .
	@#docker run --rm blong14/scrutiny pypy manage.py test --timing --settings=scrutiny.settings.spec
	@touch Dockerfile

build-go:
	@docker build -f DockerfileGo -t blong14/scrutiny-go:latest .
	@touch Dockerfile

.PHONY: check clean cover run seed shell test
check: .deps
	@python manage.py check --settings=scrutiny.settings.dev

clean:
	@echo "Cleaning dependencies..."
	@rm -rf .deps
	@rm -f scrutiny/db.sqlite3
	@pip uninstall -r requirements.txt -y

cover:
	COVERAGE_PROCESS_START=$(PWD)/.coveragerc COVERAGE_FILE=$(PWD)/.coverage PYTHONPATH=$(PWD) pytest --durations=0
	@coverage html

run: test
	@python manage.py runserver --settings=scrutiny.settings.dev

seed: .deps
	@python manage.py seed --settings=scrutiny.settings.dev

shell: .deps
	@python manage.py shell --settings=scrutiny.settings.dev

test: .deps
	@pytest --durations=0
