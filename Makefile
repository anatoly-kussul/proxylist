requirements:
	docker run -it -v $(shell pwd):/app python:3.6 bash -c "pip install -r /app/manual_requirements.txt; pip freeze > /app/build_requirements.txt"

build:
	docker build -f docker/Dockerfile -t proxylist:base .

flake:
	docker run -it -v $(shell pwd):/app:ro proxylist:base flake8 --max-line-length=120 /app *.py

test:
	docker run --rm -it -v $(shell pwd):/app proxylist:base pytest -vv tests/

coverage:
	docker run --rm -it -v $(shell pwd):/app proxylist:base bash -c "coverage run --branch --source=proxylist -m pytest -vv tests/ && coverage report -m"

python:
	docker run -it -v $(shell pwd):/app:ro proxylist:base python

run:
	docker-compose -f docker/docker-compose.yml up

stop:
	docker-compose -f docker/docker-compose.yml stop
