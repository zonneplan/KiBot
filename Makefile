#!/usr/bin/make
PY_COV=python3-coverage


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

deb_clean:
	fakeroot debian/rules clean

.PHONY: deb deb_clean lint test test_local
