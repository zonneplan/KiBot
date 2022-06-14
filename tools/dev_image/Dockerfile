FROM setsoft/kicad_debian:latest
MAINTAINER Salvador E. Tropea <set@ieee.org>
LABEL Description="KiCad with KiBot and other automation scripts"

# KiCost release
# curl -s https://api.github.com/repos/hildogjr/KiCost/releases/latest | grep "browser_download_url.*deb" | cut -d : -f 2,3 | tr -d \" | wget -i - && \

RUN     sed -i -e's/ main/ main contrib non-free/g' /etc/apt/sources.list  && \
	apt-get update  && \
	apt-get -y install -t buster-backports make wget curl rar bzip2 librsvg2-bin && \
	apt-get -y install python3-pip python3-distutils unzip && \
	apt-get -y install --no-install-recommends imagemagick python3-qrcodegen git poppler-utils ghostscript && \
	apt-get -y install --no-install-recommends python3-bs4 python3-lxml python3-tqdm && \
	curl -s https://api.github.com/repos/INTI-CMNB/KiAuto/releases/latest | grep "browser_download_url.*deb" | cut -d : -f 2,3 | tr -d \" | wget -i - && \
	curl -s https://api.github.com/repos/INTI-CMNB/KiBoM/releases/latest | grep "browser_download_url.*deb" | cut -d : -f 2,3 | tr -d \" | wget -i - && \
	curl -s https://api.github.com/repos/INTI-CMNB/InteractiveHtmlBom/releases/latest | grep "browser_download_url.*deb" | cut -d : -f 2,3 | tr -d \" | wget -i - && \
	curl -s https://api.github.com/repos/INTI-CMNB/PcbDraw/releases/latest | grep "browser_download_url.*deb" | cut -d : -f 2,3 | tr -d \" | wget -i - && \
	curl -s https://api.github.com/repos/set-soft/kicost-digikey-api-v3/releases/latest | grep "browser_download_url.*deb" | cut -d : -f 2,3 | tr -d \" | wget -i - && \
	wget https://github.com/hildogjr/KiCost/releases/download/v1.1.6/python3-validators_0.14.2-2_all.deb && \
	apt -y install --no-install-recommends ./*.deb && \
	sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<!-- <policy domain="coder" rights="none" pattern="PDF" \/> -->/g' /etc/ImageMagick-6/policy.xml && \
	sed -i 's/<policy domain="coder" rights="none" pattern="PS" \/>/<!-- <policy domain="coder" rights="none" pattern="PS" \/> -->/g' /etc/ImageMagick-6/policy.xml && \
	curl https://codeload.github.com/INTI-CMNB/KiBot/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install --no-compile KiBot-master/ && \
	rm -rf KiBot-master pp.zip && \
	curl https://codeload.github.com/hildogjr/KiCost/zip/refs/heads/master --output pp.zip && \
	unzip pp.zip && \
	pip3 install KiCost-master/ && \
	rm -rf KiCost-master pp.zip && \
	apt-get -y remove curl wget python3-pip unzip && \
	apt-get -y autoremove && \
	rm /*.deb && \
	rm -rf /var/lib/apt/lists/*
