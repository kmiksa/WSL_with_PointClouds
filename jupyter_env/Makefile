build:
	docker-compose build

bash:
	docker-compose run jupyter bash

jupyter: NOTEBOOK_URL="http://localhost:9006/lab/tree/assignment.ipynb"
jupyter:
	open ${NOTEBOOK_URL}
	docker-compose up jupyter

build-and-run:
	make build
	make jupyter