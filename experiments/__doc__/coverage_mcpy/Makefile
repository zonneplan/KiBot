#!/usr/bin/make
#PY_COV=python3-coverage
PY_COV=$(HOME)/.local/bin/coverage3

all:
	$(PY_COV) erase
	$(PY_COV) run -a  --timid ./try_mymacros.py
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html


