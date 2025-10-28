# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD := "1"
export DOCKER_BUILDKIT := "1"

# default recipe
default: down build up test

# build docker images
build:
	docker-compose build

# start app service
up:
	docker-compose up -d app

# stop and remove containers
down:
	docker-compose down --remove-orphans

# run all tests
test: up
	docker-compose run --rm --no-deps --entrypoint="uv run pytest" app /tests/unit /tests/integration /tests/e2e

# run unit tests only
unit-tests:
	docker-compose run --rm --no-deps --entrypoint="uv run pytest" app /tests/unit

# run failed tests
failed-tests:
	docker-compose run --rm --no-deps --entrypoint="uv run pytest --lf -vvv" app /tests/unit /tests/integration /tests/e2e

# run integration tests
integration-tests: up
	docker-compose run --rm --no-deps --entrypoint="uv run pytest" app /tests/integration

# run e2e tests
e2e-tests: up
	docker-compose run --rm --entrypoint="uv run pytest" app /tests/e2e

# run specific tests matching a pattern
test-k pattern: up
	docker-compose run --rm --no-deps --entrypoint="uv run pytest -k {{pattern}}" app /tests/unit /tests/integration /tests/e2e

# show app logs
logs:
	docker-compose logs app | tail -100

# format python files with black
black:
	black -l 86 $(find * -name '*.py')
