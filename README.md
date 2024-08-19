# Cosmic Python

Este repo contiene ejercicios/comentarios/etc que acompañan al libro https://www.cosmicpython.com

El repo incluye branches por cada capítulo pero yo tomé otro approach.

1. Empecé con la rama `chapter_01_domain_model_exercise`
1. Al finalizar con ese chapter, taggeo el commit `git tag -a 0.1 -m "Ch 01 - Domain modeling"` y `git push --follow-tags`
1. Sigo trabajando en la misma rama y a medida que avanzo mergeo las ramas de los otros capítulos
    ```bash
    > git status
    ... branch chapter_01_domain_model_exercise
    > git merge chapter_0x
    ```

## Estructura

-   `domain`: Currently that’s just one file, but for a more complex application, you might have one file per class; you might have helper parent classes for Entity, ValueObject, and Aggregate, and you might add an exceptions.py for domain-layer exceptions, commands.py and events.py.
-   `service_layer`: Currently that’s just one file called services.py for our service-layer functions.
-   `adapters`: is a nod to the ports and adapters terminology. This will fill up with any other abstractions around external I/O (e.g., a redis_client.py).
-   `entrypoints`: the places we drive our application from.

## Notas

Mis notas en [Notion](https://marcorichetta.notion.site/Cosmic-Python-ba8357d1ede943df909c10fb4b518fff?pvs=4)

---

### Original readme

---

## Chapters

Each chapter has its own branch which contains all the commits for that chapter,
so it has the state that corresponds to the _end_ of that chapter. If you want
to try and code along with a chapter, you'll want to check out the branch for the
previous chapter.

https://github.com/python-leap/code/branches/all

## Exercises

Branches for the exercises follow the convention `{chatper_name}_exercise`, eg
https://github.com/python-leap/code/tree/chapter_04_service_layer_exercise

## Requirements

-   docker with docker-compose
-   for chapters 1 and 2, and optionally for the rest: a local python3.7 virtualenv

## Building the containers

_(this is only required from chapter 3 onwards)_

```sh
make build
make up
# or
make all # builds, brings containers up, runs tests
```

## Creating a local virtualenv (optional)

```sh
python3.8 -m venv .venv && source .venv/bin/activate # or however you like to create virtualenvs

# for chapter 1
pip install pytest

# for chapter 2
pip install pytest sqlalchemy

# for chapter 4+5
pip install requirements.txt

# for chapter 6+
pip install requirements.txt
pip install -e src/
```

<!-- TODO: use a make pipinstall command -->

## Running the tests

```sh
make test
# or, to run individual test types
make unit
make integration
make e2e
# or, if you have a local virtualenv
make up
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

## Makefile

There are more useful commands in the makefile, have a look and try them out.
