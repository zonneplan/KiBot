# Blender experiments

The [pcb2blender](https://github.com/30350n/pcb2blender) plug-in allows
importing KiCad PCBs in Blender.

It has two parts:

- Exporter: A KiCad 6 action plug-in to export the PCB
- Importer: A Blender 3.4 + Python 10 plug-in for Blender

A user called @Haschtl asked for VRML export in issue #349.
Its objetive was to convert KiCad PCBs into
[GLTF](https://es.wikipedia.org/wiki/GlTF), a portable 3D
format, to be displayed in web pages. This format can
be used to render good quality 3D models in web pages,
here is an [example](https://github.khronos.org/glTF-Sample-Viewer-Release/).

@Haschtl has its own [fork](https://github.com/haschtl/pcb2blender)
where he is experimenting with some changes to the original plug-in in
order to make the 3D models easier to render, at the cost of some quality.

As Blender is scriptable generating the files for the Blender plug-in
opens various interesting uses.

So I started to investigate it. Currently (2023/01/08) the current KiBot `dev`
branch can generate files for both plug-ins (the original and the fork).

This document is just some information about what I experimented.

## Blender requirements

This is a really complex thing @30350n coded the pluig-in for the last version
of Blender (3.4.x), the current Blender for Debian stable is 2.83 and for
testing/unstable 3.3.x. To make things worst he coded it using Python 3.10
syntax (Python 3.9 is the one in Debian stable).

Even removing the Python 3.10 extensions I found that Blender 2.83 can't handle
the VRML files as expected.

Using Blender 3.3.5 from `bookworm` (current testing) is enough.
I tried to setup docker images to test the import plug-in.

### Linux Server images

This project has Blender [images](https://hub.docker.com/r/linuxserver/blender).
The current latest was 3.4.1.
The images are easy to use ... well ... once you figure out how they think.

You must first pull the image:

```
docker pull lscr.io/linuxserver/blender:latest
```

This is a 1.82 GB docker image.
Once you have the image you must create a directory to store Blender config,
lets say:

```
mkdir ~/blender_docker_config/
```

Now you can run the image using something like this:

```
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
export TZ=$(cat /etc/timezone)
docker run -d \
  --name=blender \
  -e PUID=$USER_ID \
  -e PGID=$GROUP_ID \
  -e TZ=$TZ \
  -p 3000:3000 \
  -v /home/$USER/blender_docker_config/:/config \
  --device /dev/dri:/dev/dri \
  --restart unless-stopped \
  lscr.io/linuxserver/blender:latest
```

This creates a container that will be **always** running on your system,
unless you explicitly run `docker stop blender`. The container runs in
background (-d).

To access to the GUI you can just open `http://localhost:3000` in your
browser. This looks really simple, but at least in my case, using a 4k
display, Blender is really hard to use.

I tried to use it connecting to my DISPLAY, but couldn't. The image uses
some bogus user and has some particular setup.

The documentation for these images is [here](https://docs.linuxserver.io/),
and the Dockerfile is available at
[GitHub](https://github.com/linuxserver/docker-blender).

Note that in order to install the plug-in you need `pip`, which **isn't**
included in the image. You must get and run the `get-pip.py` script from
the [pip documentation](https://pip.pypa.io/en/stable/installation/).

### rd-blender-docker

These images are available at [GitHub](https://github.com/nytimes/rd-blender-docker).
The current version was 3.3.1, which seems to be good enough for the
plug-in.

The images comes in two flavors: with and without support for GPU render.
I tried the GPU version, but I don't have the needed proprietary drivers
installed. The GPU image is 1.69 GB and you can get it pulling:

```
docker pull nytimes/blender:latest
```

This image is much more simple and I was able to run it with good performance.
I just run it using my HOME directory for it, like this:

```
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
export TZ=$(cat /etc/timezone)
docker run -it --rm \
  --user $USER_ID:$GROUP_ID \
  --env TZ=$TZ \
  --env DISPLAY=$DISPLAY \
  --env NO_AT_BRIDGE=1 \
  --workdir="/home/$USER" \
  --volume="/tmp/.X11-unix:/tmp/.X11-unix" \
  --volume="/etc/group:/etc/group:ro" \
  --volume="/home/$USER:/home/$USER:rw" \
  --volume="/etc/passwd:/etc/passwd:ro" \
  --volume="/etc/shadow:/etc/shadow:ro" \
  --volume="/home/$USER:/home/$USER:rw" \
  --device /dev/dri:/dev/dri \
  nytimes/blender:latest blender
```

Note that this maps all the system users into the docker image.
As this connects to the X display using your authorization and as we map the
DRI device the speed is good.

The version without GPU support is 1.43 GB.

Note that this image contains `pip`.

The bad thing about these images is that they are created installing the
Blender tarball from [here](https://mirror.clarkson.edu/blender/release/),
making it bad to integrate with other tools.


### Blender for Debian

I tried creating a docker image using Debian.
It needs bookworm (testing) to get Blender 3.3.1.
I used:

```
FROM debian:bookworm-slim
MAINTAINER Salvador E. Tropea <stropea@inti.gob.ar>
LABEL Description="Minimal Blender image based on Debian"

RUN     apt-get -y update && \
	apt-get -y install --no-install-recommends blender && \
	apt-get -y install --no-install-recommends python3-pip python3-pil && \
	apt-get -y install --no-install-recommends python3-numpy && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/* \
	rm -rf /usr/share/icons/Adwaita/
```

It works ... but I found Blender is compiled without the Intel denoiser.
So renders using Cycle renderer fails, you have to disable the denoiser.
I don't know why Blender enables something not compiled.
Anyways, without the denoiser a 1 minute render could take an hour.
Basically: this package is pointless.


### Blender for Ubuntu

I tried using lunar, to get 3.3.1. I used:

```
FROM ubuntu:lunar
MAINTAINER Salvador E. Tropea <stropea@inti.gob.ar>
LABEL Description="Minimal Blender image based on Ubuntu"

RUN     apt-get -y update && \
	apt-get -y install --no-install-recommends blender && \
	apt-get -y install --no-install-recommends python3-pip python3-pil python3-numpy && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/* \
	rm -rf /usr/share/icons/Adwaita/
```

And got *blender: symbol lookup error: blender: undefined symbol:
_ZN7openvdb4v9_16points14AttributeArrayC2ERKS2_RKN3tbb6detail2d118unique_scoped_lockINS7_10spin_mutexEEE*

Looks like at the moment the package is broken.

### Custom solution

From the experiments I conclude:

- Support for Blender in Debian is weak (broken)
- Workable images uses the tarball

So I decided to integrate it with my current Debian stable + KiCad images

#### Installing Blender

It must be installed from the tarball, but I don't like it on */bin* like in
rd-blender-docker images. So I installed it on `/usr/bin`

```docker
RUN     apt-get -y update && \
        apt-get -y install --no-install-recommends xz-utils wget && \
        wget https://mirrors.ocf.berkeley.edu/blender/release/Blender3.4/blender-3.4.1-linux-x64.tar.xz && \
        tar xvf blender-3.4.1-linux-x64.tar.xz --strip-components=1 -C /usr/bin/ && \
        rm blender-3.4.1-linux-x64.tar.xz && \
        apt-get -y remove wget xz-utils && \
        apt-get -y autoremove && \
        rm -rf /var/lib/apt/lists/*
```

It provides an usable Blender, a lot of static stuff, some system X libs and a
few custom libs:

```shell
$ ldd `which blender`
	linux-vdso.so.1 (0x00007ffd2bfd0000)
	librt.so.1 => /lib/x86_64-linux-gnu/librt.so.1 (0x00007fcbb9943000)
	libutil.so.1 => /lib/x86_64-linux-gnu/libutil.so.1 (0x00007fcbb993e000)
	libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007fcbb991c000)
	libdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007fcbb9916000)
	libX11.so.6 => /usr/lib/x86_64-linux-gnu/libX11.so.6 (0x00007fcbb97d3000)
	libXrender.so.1 => /usr/lib/x86_64-linux-gnu/libXrender.so.1 (0x00007fcbb95c9000)
	libXxf86vm.so.1 => /usr/lib/x86_64-linux-gnu/libXxf86vm.so.1 (0x00007fcbb93c1000)
	libXfixes.so.3 => /usr/lib/x86_64-linux-gnu/libXfixes.so.3 (0x00007fcbb93b9000)
	libXi.so.6 => /usr/lib/x86_64-linux-gnu/libXi.so.6 (0x00007fcbb93a7000)
	libxkbcommon.so.0 => /usr/lib/x86_64-linux-gnu/libxkbcommon.so.0 (0x00007fcbb9364000)
	libcycles_kernel_oneapi_aot.so => /usr/bin/lib/libcycles_kernel_oneapi_aot.so (0x00007fcbb4268000)
	libsycl.so.6 => /usr/bin/lib/libsycl.so.6 (0x00007fcbb3e20000)
	libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x00007fcbb3cda000)
	libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fcbb3b05000)
	/lib64/ld-linux-x86-64.so.2 (0x00007fcbb9959000)
	libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1 (0x00007fcbb3aeb000)
	libxcb.so.1 => /usr/lib/x86_64-linux-gnu/libxcb.so.1 (0x00007fcbb3ac0000)
	libXext.so.6 => /usr/lib/x86_64-linux-gnu/libXext.so.6 (0x00007fcbb3aab000)
	libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 (0x00007fcbb38dc000)
	libXau.so.6 => /usr/lib/x86_64-linux-gnu/libXau.so.6 (0x00007fcbb38d7000)
	libXdmcp.so.6 => /usr/lib/x86_64-linux-gnu/libXdmcp.so.6 (0x00007fcbb36d1000)
	libbsd.so.0 => /usr/lib/x86_64-linux-gnu/libbsd.so.0 (0x00007fcbb36ba000)
	libmd.so.0 => /usr/lib/x86_64-linux-gnu/libmd.so.0 (0x00007fcbb36ad000)
```

#### Installing plug-in dependencies

They must be installed in the Python copy embeded in Blender.
We must install `pip`, I don't understand why the Blender people doesn't
include it.
After installing `pip` we need `pillow` and `skia-python`.

```docker
RUN     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
        /usr/bin/3.4/python/bin/python3.10 get-pip.py && \
        /usr/bin/3.4/python/bin/python3.10 -m pip install pillow && \
        /usr/bin/3.4/python/bin/python3.10 -m pip install skia-python
```

#### Installing the plug-in

We need to install it, but the normal installation is on the user's home,
quite pointless here. Is amazing how these mature tools doens't provide
clean mechanisms for system level plug-ins.

In order to install the plug-in we need to use a Python script, like this:

```python
import bpy

# Register the addon and enable it
bpy.context.preferences.filepaths.script_directory = '/usr/bin/3.4/scripts/'
bpy.ops.preferences.addon_install(filepath='./pcb2blender_importer_2-1.zip', target='PREFS')
bpy.ops.preferences.addon_enable(module='pcb2blender_importer')
bpy.ops.wm.save_userpref()
```

This configures the script directory as */usr/bin/3.4/scripts/*, which is the
place where the bundled plug-ins are installed. Then we install the plu-in
using the previous dir as target. We finally enable the plug-in and save the
user config. This save the config for the root. This is ok when using CI/CD,
we use root as user. It isn't really good when we want to run the Blender
inside the image for a regular user. In this case the user must enable the
plug-in manually. Ridiculous, and very Windows style.

The docker part is: (enable_pcb2blender.py is the previous Python code)

```docker
RUN     curl -L https://github.com/30350n/pcb2blender/releases/download/v2.1-k6.0-b3.4/pcb2blender_importer_2-1.zip -o pcb2blender_importer_2-1.zip && \
        blender --background --python /usr/bin/enable_pcb2blender.py && \
        rm pcb2blender_importer_2-1.zip
```

#### All together

```docker
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
	/usr/bin/3.4/python/bin/python3.10 -m pip install pillow && \
	/usr/bin/3.4/python/bin/python3.10 -m pip install skia-python
# Install the plug-in
COPY  enable_pcb2blender.py /usr/bin/
RUN     curl -L https://github.com/30350n/pcb2blender/releases/download/v2.1-k6.0-b3.4/pcb2blender_importer_2-1.zip -o pcb2blender_importer_2-1.zip && \
	blender --background --python /usr/bin/enable_pcb2blender.py && \
	rm pcb2blender_importer_2-1.zip
```

Built with:

```shell
#!/bin/sh
docker build -f Dockerfile -t setsoft/kicad_auto_test_blender:latest .
```

Using `enable_pcb2blender.py`:

```python
import bpy

# Register the addon and enable it
bpy.context.preferences.filepaths.script_directory = '/usr/bin/3.4/scripts/'
bpy.ops.preferences.addon_install(filepath='./pcb2blender_importer_2-1.zip', target='PREFS')
bpy.ops.preferences.addon_enable(module='pcb2blender_importer')
bpy.ops.wm.save_userpref()
```

We can then run Blender 3.4.1 on the host using:

```shell
#!/bin/bash
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
export TZ=$(cat /etc/timezone)
docker run -it --rm \
  --user $USER_ID:$GROUP_ID \
  --env TZ=$TZ \
  --env DISPLAY=$DISPLAY \
  --env NO_AT_BRIDGE=1 \
  --workdir="/home/$USER" \
  --volume="/tmp/.X11-unix:/tmp/.X11-unix" \
  --volume="/etc/group:/etc/group:ro" \
  --volume="/home/$USER:/home/$USER:rw" \
  --volume="/etc/passwd:/etc/passwd:ro" \
  --volume="/etc/shadow:/etc/shadow:ro" \
  --volume="/home/$USER:/home/$USER:rw" \
  --device /dev/dri:/dev/dri \
  setsoft/kicad_auto_test_blender:latest blender
```

Remmeber you must enable the plug-in manually in Edit | Preferences | Add-ons
searching for `pcb2blender`. This is persistent because we mounted the user
home. The config will be stored in `~/.config/blender/3.4/`.

The resulting image is huge. About 2.77 GB, the tarball adds 943 MB and the
Python dependencies 167 MB. About 1.1 GB added. The price of installing
things in a dirty way.

#### Numpy issues

I'm not sure why but skia pulls numpy (isn't it part of Blender bundles?)
The problem is that it pulls 1.24.1 and the glTF importer uses `numpy.bool`,
deprecated in 1.20 and changed to `numpy.bool_`.

So I ended forcing 1.23.1


## Using Blender from the docker image

To pretend this is the system level Blender I have:

```shell
#!/bin/bash
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
docker run --rm \
  --user $USER_ID:$GROUP_ID \
  --env DISPLAY=$DISPLAY \
  --env NO_AT_BRIDGE=1 \
  --workdir=$(pwd) \
  --volume="/tmp:/tmp" \
  --volume="/etc/group:/etc/group:ro" \
  --volume="/etc/gshadow:/etc/gshadow:ro" \
  --volume="/etc/timezone:/etc/timezone:ro" \
  --volume="/home/$USER:/home/$USER:rw" \
  --volume="/etc/passwd:/etc/passwd:ro" \
  --volume="/etc/shadow:/etc/shadow:ro" \
  --volume="/home/$USER:/home/$USER:rw" \
  --device /dev/dri:/dev/dri \
  setsoft/kicad_auto_test_blender:latest nice blender "$@"
```

Named *blender* in my path (~/bin/blender).
In this way running `blender` gives me Blender 3.4.1, and not 2.83.5 (from the
system).
