#!/bin/sh
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
  setsoft/kicad_auto_test_blender:latest /bin/bash

