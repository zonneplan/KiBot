#!/usr/bin/make
PY_COV?=python3-coverage
PYTEST?=pytest-3
REFDIR=tests/reference/5_1_7/
REFILL=tests/board_samples/zone-refill.kicad_pcb
CWD := $(abspath $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST))))))
USER_ID=$(shell id -u)
GROUP_ID=$(shell id -g)

ifneq ("$(wildcard *.yaml)","")
$(error Move away any config file)
endif

ifneq ("$(wildcard *.sch)","")
$(error Move away any schematic file)
endif

ifneq ("$(wildcard tests/board_samples/bom.xml-bak*)","")
$(error Revert tests/board_samples/bom.xml-bak)
endif

deb:
	DEB_BUILD_OPTIONS=nocheck fakeroot dpkg-buildpackage -uc -b

deb_sig:
	DEB_BUILD_OPTIONS=nocheck fakeroot dpkg-buildpackage -b

lint: doc
	# flake8 --filename is broken
	ln -sf src/kiplot kiplot.py
	ln -sf src/kibot kibot.py
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	pre-commit run -a
	rm kiplot.py
	rm kibot.py

test_tmp: lint
	$(PY_COV) erase
	$(PYTEST)
	$(PY_COV) combine
	$(PY_COV) report

test: lint
	rm -rf output
	rm -f example.kiplot.yaml
	rm -f example.kibot.yaml
	rm -f tests/.local
	$(PY_COV) erase
	$(PYTEST) -m "not slow" -n 2 --test_dir=output
	$(PYTEST) -m "slow" --test_dir=output
	$(PY_COV) combine
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html

test1:
	rm -rf output
	rm -f example.kiplot.yaml
	rm -f example.kibot.yaml
	rm -f tests/.local
	$(PY_COV) erase
	$(PYTEST) --log-cli-level debug -k "test_bom_ok" --test_dir=output
	$(PY_COV) combine
	$(PY_COV) report
	$(PY_COV) html
	#x-www-browser htmlcov/index.html
	@echo "********************" Output
	@cat output/*/output.txt
	#@echo "********************" Error
	#@cat output/*/error.txt

t1k5: test_docker_local_1

test_docker_local_1:
	-rm -rf output
	-rm -f tests/.local
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	#docker run --rm -it -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:latest '/bin/bash'
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:latest \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run -a src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/board_samples/ tests/.config/kiplot/plugins/__pycache__/ tests/test_plot/fake_pcbnew/__pycache__/ tests/.config/kibot/plugins/__pycache__/ .coverage.* htmlcov/"
	#$(PY_COV) report
	#x-www-browser htmlcov/index.html
	# The coverage used in the image is incompatible
	#$(PY_COV) erase

test_docker_local_1_ki6:
	rm -rf output
	rm -f tests/.local
	#$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:ki6 \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k 'test_dep_pytool' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/board_samples/ tests/.config/kiplot/plugins/__pycache__/ tests/test_plot/fake_pcbnew/__pycache__/ tests/.config/kibot/plugins/__pycache__/ .coverage htmlcov/"
	#$(PY_COV) report
	#x-www-browser htmlcov/index.html

test_docker_local:
	rm -rf output
	rm -f tests/.local
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:latest \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs ; pytest-3 --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/board_samples/ .coverage htmlcov/"
	$(PY_COV) combine
	$(PY_COV) report
	x-www-browser htmlcov/index.html

test_docker_local_ki6:
	rm -rf output
	rm -f tests/.local
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:ki6 \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs ; pytest-3 --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/board_samples/ .coverage htmlcov/"
	$(PY_COV) combine
	$(PY_COV) report
	x-www-browser htmlcov/index.html

docker_shell:
	docker run  -it --rm -v $(CWD):$(CWD) --workdir="$(CWD)" \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$(DISPLAY) \
	--user $(USER_ID):$(GROUP_ID) \
	--volume="/etc/group:/etc/group:ro" \
	--volume="/etc/passwd:/etc/passwd:ro" \
	--volume="/etc/shadow:/etc/shadow:ro" \
	--volume="/home/$(USER):/home/$(USER):rw" \
	setsoft/kicad_auto_test:latest /bin/bash

t1k6: single_test

single_test:
	rm -rf pp
	-$(PY_COV) run src/kibot --help-list-outputs > /dev/null
	-$(PYTEST) --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir=pp
	@echo "********************" Output
	@cat pp/*/output.txt
	@echo "********************" Error
	@tail -n 30 pp/*/error.txt
	@rm -f tests/input_samples/bom.ini

single_tests:
	rm -rf pp
	# 12 threads, for a 6 core CPU w/HT. Almost 4 times faster for BoM tests.
	-$(PYTEST) -n 12 --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir=pp
	@rm -f tests/input_samples/bom.ini

deb_clean:
	fakeroot debian/rules clean

gen_ref:
	# Reference outputs, must be manually inspected if regenerated
	pcbnew_do export --output_name bom-F_Cu+F_SilkS.pdf --scaling 4 --pads 0 --no-title --monochrome --separate tests/board_samples/bom.kicad_pcb $(REFDIR) F.Cu F.SilkS
	cp -a $(REFILL).refill $(REFILL)
	src/kibot -c tests/yaml_samples/pdf_zone-refill.kibot.yaml -b tests/board_samples/zone-refill.kicad_pcb -d $(REFDIR)
	src/kibot -c tests/yaml_samples/print_pcb_zone-refill.kibot.yaml -b tests/board_samples/zone-refill.kicad_pcb -d $(REFDIR)
	src/kibot -c tests/yaml_samples/print_pdf_no_inductors_1.kibot.yaml -e tests/board_samples/test_v5.sch -d $(REFDIR)
	mv "$(REFDIR)no_inductor/test_v5-schematic_(no_L).pdf" $(REFDIR)
	rmdir $(REFDIR)no_inductor/
	src/kibot -c tests/yaml_samples/print_svg_no_inductors_1.kibot.yaml -e tests/board_samples/test_v5.sch -d $(REFDIR)
	mv "$(REFDIR)no_inductor/test_v5-schematic_(no_L).svg" $(REFDIR)
	-@rm -rf $(REFDIR)no_inductor/
	src/kibot -b tests/board_samples/kibom-variant_4.kicad_pcb -c tests/yaml_samples/pdf_variant_1.kibot.yaml -d $(REFDIR)
	src/kibot -b tests/board_samples/kibom-variant_3.kicad_pcb -c tests/yaml_samples/pcbdraw_variant_1.kibot.yaml -d $(REFDIR)
	src/kibot -b tests/board_samples/kibom-variant_3.kicad_pcb -c tests/yaml_samples/pcbdraw_variant_2.kibot.yaml -d $(REFDIR)
	src/kibot -b tests/board_samples/kibom-variant_3.kicad_pcb -c tests/yaml_samples/print_pcb_variant_1.kibot.yaml -d $(REFDIR)
	cp -a $(REFILL).ok $(REFILL)

doc:
	make -C docs

py_build:
	python3 setup.py sdist bdist_wheel

pypi_upload: py_clean py_build
	python3 -m twine upload dist/*

py_clean:
	@rm -rf .pybuild build dist kibot.egg-info

.PHONY: deb deb_clean lint test test_local gen_ref doc py_build pypi_upload py_clean
