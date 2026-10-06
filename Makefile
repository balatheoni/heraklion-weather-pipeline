.PHONY: install ingest test train all docker

install:
	pip install -r requirements.txt

ingest:
	python ingestion.py

test:
	pytest -q

train:
	python train.py

all: ingest test train

docker:
	docker build -t heraklion-weather .
	docker run --rm -v "$(CURDIR)":/app heraklion-weather
