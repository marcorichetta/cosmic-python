# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD := "1"
export DOCKER_BUILDKIT := "1"

# default recipe
default: down build up test

# build docker images
build:
	docker-compose build

# start api service
up:
	docker-compose up -d

# stop and remove containers
down:
	docker-compose down --remove-orphans

# run all tests
test: up
	docker-compose run --rm --no-deps --entrypoint="uv run pytest" api /tests/unit /tests/integration /tests/e2e

# run unit tests only
unit-tests:
	docker-compose run --rm --no-deps --entrypoint="uv run pytest" api /tests/unit

# run failed tests
failed-tests:
	docker-compose run --rm --no-deps --entrypoint="uv run pytest --lf -vvv" api /tests/unit /tests/integration /tests/e2e

# run integration tests
integration-tests: up
	docker-compose run --rm --no-deps --entrypoint="uv run pytest" api /tests/integration

# run e2e tests
e2e-tests: up
	docker-compose run --rm --entrypoint="uv run pytest" api /tests/e2e

# run specific tests matching a pattern
test-k pattern: up
	docker-compose run --rm --no-deps --entrypoint="uv run pytest -k {{pattern}}" api /tests/unit /tests/integration /tests/e2e

# show api logs
logs:
	docker-compose logs --tail=25 api redis_pubsub


# format python files with black
black:
	black -l 86 $(find * -name '*.py')
