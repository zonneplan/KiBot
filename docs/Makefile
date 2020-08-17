#!/usr/bin/make

all: ../README.md  samples/generic_plot.kibot.yaml

../README.md: README.in replace_tags.pl ../kibot/out_*.py ../kibot/pre_*.py ../kibot/__main__.py ../kibot/config_reader.py
	cat README.in | perl replace_tags.pl > ../README.md

samples/generic_plot.kibot.yaml: ../kibot/out_*.py ../kibot/pre_*.py ../kibot/config_reader.py
	rm -f example.kibot.yaml
	../src/kibot --example
	mv example.kibot.yaml $@
