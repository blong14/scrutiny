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

.PHONY: build check clean cover run shell test
build:
	@docker build -t blong14/scrutiny:latest .
	@docker run --rm blong14/scrutiny pypy manage.py test --timing --settings=scrutiny.settings.spec

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

shell: .deps
	@python manage.py shell --settings=scrutiny.settings.dev

test: .deps
	@pytest --durations=0
