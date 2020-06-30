#!/usr/bin/make

all: ../README.md  samples/generic_plot.kiplot.yaml

../README.md: README.in replace_tags.pl ../kiplot/out_*.py ../kiplot/pre_*.py ../kiplot/__main__.py
	cat README.in | perl replace_tags.pl > ../README.md

samples/generic_plot.kiplot.yaml: ../kiplot/out_*.py ../kiplot/pre_*.py ../kiplot/config_reader.py
	../src/kiplot --example
	mv example.kiplot.yaml $@
