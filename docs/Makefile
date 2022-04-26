#!/usr/bin/make

all: ../README.md  samples/generic_plot.kibot.yaml ../kibot/report_templates/report_full_svg.txt ../kibot/config_templates/bom/MacroFab_XYRS.kibot.yaml \
	../kibot/config_templates/gerber/Elecrow.kibot.yaml ../kibot/config_templates/gerber/FusionPCB.kibot.yaml \
	../kibot/config_templates/gerber/JLCPCB.kibot.yaml ../kibot/config_templates/gerber/PCBWay.kibot.yaml

../kibot/config_templates/gerber/%.kibot.yaml: samples/%.kibot.yaml
	cp $< $@

../kibot/config_templates/bom/%.kibot.yaml: samples/%.kibot.yaml
	cp $< $@

../README.md: README.in replace_tags.pl ../kibot/out_*.py ../kibot/pre_*.py ../kibot/fil_*.py ../kibot/__main__.py ../kibot/config_reader.py
	cat README.in | perl replace_tags.pl > ../README.md

samples/generic_plot.kibot.yaml: ../kibot/out_*.py ../kibot/pre_*.py ../kibot/config_reader.py
	rm -f example_template.kibot.yaml
	../src/kibot -v --example
	mv example_template.kibot.yaml $@

../kibot/report_templates/report_full_svg.txt: ../kibot/report_templates/report_full.txt
	sed -e 's/layer_pdfs/layer_svgs/' $< > $@
