#
# Makefile
#

MODULE = clear

# Install packages from requirements file
.PHONY: init
init:
	pip install -r requirements.txt

# Build source and wheel distributions
.PHONY: build
build:
	python setup.py sdist
	python setup.py bdist_wheel

# Upload using twine
.PHONY: upload
upload:
	twine upload dist/*

# Execute tests in a clean virtual environment
.PHONY: runtest
runtest:
	echo "VIRTUAL ENVIRONMENT SETUP:"; \
	virtualenv --clear testenv; \
	source ./testenv/bin/activate; \
	pip install -e .; \
	echo "\nRUNNING TEST SUITE:"; \
	python -m unittest discover -v ./tests; \
	deactivate; \
	rm -rf testenv; \

# Generate coverage
.PHONY: coverage
coverage:
	echo "VIRTUAL ENVIRONMENT SETUP:"; \
	virtualenv --clear covenv; \
	source ./covenv/bin/activate; \
	pip install -e .; \
	pip install coverage; \
	echo "\nRUNNING TEST SUITE WITH COVERAGE:"; \
	coverage run -m unittest discover -v ./tests; \
	coverage html; \
	deactivate; \
	rm -rf covenv; \
