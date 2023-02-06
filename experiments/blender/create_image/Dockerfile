FROM setsoft/kicad_auto_test:ki6
MAINTAINER Salvador E. Tropea <stropea@inti.gob.ar>
LABEL Description="KiBot full + Blender on Debian"

# Install Blender
RUN     apt-get -y update && \
	apt-get -y install --no-install-recommends xz-utils wget && \
	wget https://mirrors.ocf.berkeley.edu/blender/release/Blender3.4/blender-3.4.1-linux-x64.tar.xz && \
	tar xvf blender-3.4.1-linux-x64.tar.xz --strip-components=1 -C /usr/bin/ && \
	rm blender-3.4.1-linux-x64.tar.xz && \
	apt-get -y remove wget xz-utils && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/*
# Install plug-in deps: pillow and skia-python (pip, numpy, etc.)
RUN     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
	/usr/bin/3.4/python/bin/python3.10 get-pip.py && \
	/usr/bin/3.4/python/bin/python3.10 -m pip install numpy==1.23.1 && \
	/usr/bin/3.4/python/bin/python3.10 -m pip install pillow && \
	/usr/bin/3.4/python/bin/python3.10 -m pip install skia-python && \
	rm get-pip.py
# Install the plug-in
COPY  enable_pcb2blender.py /usr/bin/
RUN     curl -L https://github.com/30350n/pcb2blender/releases/download/v2.1-k6.0-b3.4/pcb2blender_importer_2-1.zip -o pcb2blender_importer_2-1.zip && \
	blender --background --python /usr/bin/enable_pcb2blender.py && \
	rm pcb2blender_importer_2-1.zip

