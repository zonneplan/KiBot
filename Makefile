#!/usr/bin/make
PY_COV=python3-coverage
REFDIR=tests/reference/
REFILL=tests/board_samples/zone-refill.kicad_pcb
CWD := $(abspath $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST))))))
USER_ID=$(shell id -u)
GROUP_ID=$(shell id -g)

deb:
	fakeroot dpkg-buildpackage -uc -b

lint:
	# flake8 --filename is broken
	ln -sf src/kiplot kiplot.py
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --statistics
	rm kiplot.py

test: lint
	$(PY_COV) erase
	pytest-3
	$(PY_COV) report

test_local: lint
	rm -rf output
	$(PY_COV) erase
	pytest-3 --test_dir output
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html

test_docker_local:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:latest \
		/bin/bash -c "flake8 . --count --statistics ; pytest-3 --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/board_samples/"
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html

deb_clean:
	fakeroot debian/rules clean

gen_ref:
	# Reference outputs, must be manually inspected if regenerated
	cp -a $(REFILL).refill $(REFILL)
	src/kiplot -c tests/yaml_samples/pdf_zone-refill.kiplot.yaml -b tests/board_samples/zone-refill.kicad_pcb -d $(REFDIR)
	src/kiplot -c tests/yaml_samples/print_pcb_zone-refill.kiplot.yaml -b tests/board_samples/zone-refill.kicad_pcb -d $(REFDIR)
	cp -a $(REFILL).ok $(REFILL)

.PHONY: deb deb_clean lint test test_local gen_ref
