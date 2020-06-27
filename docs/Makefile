#!/usr/bin/make

all: ../README.md

../README.md: README.in replace_tags.pl ../kiplot/out_*.py ../kiplot/pre_*.py ../kiplot/__main__.py
	cat README.in | perl replace_tags.pl > ../README.md

