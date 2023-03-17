#!/bin/sh
set -e
docker build -f Dockerfile -t ghcr.io/inti-cmnb/kicad7_auto_full:dev .
TG1=`docker run --rm ghcr.io/inti-cmnb/kicad7_auto_full:dev kibot --version | sed 's/.* \([0-9]\+\.[0-9]\+\.[0-9]\+\) .*/\1/' | tr -d '\n'`
HASH=`git log --pretty=format:%h -1 | tr -d '\n'`
TG2=k`docker run --rm ghcr.io/inti-cmnb/kicad7_auto_full:dev kicad_version.py`
TG3=d`docker run --rm ghcr.io/inti-cmnb/kicad7_auto_full:dev cat /etc/debian_version | tr -d '\n'`
TG4=b`docker run --rm ghcr.io/inti-cmnb/kicad7_auto_full:latest /bin/bash -c "ls -d /usr/bin/?.? | tr -d '\n' | tail -c 3"`
docker tag ghcr.io/inti-cmnb/kicad7_auto_full:dev ghcr.io/inti-cmnb/kicad7_auto_full:dev_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker tag ghcr.io/inti-cmnb/kicad7_auto_full:dev ghcr.io/inti-cmnb/kicad_auto_full:dev_k7_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker tag ghcr.io/inti-cmnb/kicad7_auto_full:dev ghcr.io/inti-cmnb/kicad_auto_full:dev_k7
docker push ghcr.io/inti-cmnb/kicad7_auto_full:dev_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker push ghcr.io/inti-cmnb/kicad_auto_full:dev_k7_${TG1}-${HASH}_${TG2}_${TG3}_${TG4}
docker push ghcr.io/inti-cmnb/kicad_auto_full:dev_k7
docker push ghcr.io/inti-cmnb/kicad7_auto_full:dev
