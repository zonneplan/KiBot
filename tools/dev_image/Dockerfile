FROM setsoft/kicad_auto:latest
MAINTAINER Salvador E. Tropea <stropea@inti.gob.ar>
LABEL Description="KiCad 5 with KiBot and other automation scripts"

RUN     dpkg --remove kicost kibot kiauto && \
	apt-get update && \
	apt-get -y install --no-install-recommends python3-pip unzip curl python3-setuptools python3-wheel && \
	curl https://codeload.github.com/INTI-CMNB/KiBot/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install --no-compile KiBot-master/ && \
	rm -rf KiBot-master pp.zip && \
	curl https://codeload.github.com/hildogjr/KiCost/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install KiCost-master/ && \
	rm -rf KiCost-master pp.zip && \
	curl https://codeload.github.com/INTI-CMNB/KiAuto/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install KiAuto-master/ && \
	rm -rf KiAuto-master/ pp.zip && \
	apt-get -y remove curl python3-pip unzip python3-setuptools python3-wheel && \
	rm -rf /var/lib/apt/lists/*
