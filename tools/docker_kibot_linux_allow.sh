#!/bin/bash
# Two optional arguments, first is the command to run, the second the image name
cmd=/bin/bash
image=kicad8_auto_full:latest

# Check for optional arguments
if [ ! -z "$1" ]; then
    cmd="$1"
fi

if [ ! -z "$2" ]; then
    image="$2"
fi


# Save current xhost access control state to a variable
original_state=$(xhost)

# Add access for the local user
allow_to=SI:localuser:$USER
added_access="false"
if [[ "$original_state" == *"access control disabled"* || "$original_state" == *"$allow_to"* ]]; then
    echo "The user already has access."
else
    echo "Adding access for " $allow_to " ..."
    xhost +$allow_to
    added_access="true"
fi

# Start the docker container
echo "Starting " $image " ..."
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
docker run --rm -it \
    --user $USER_ID:$GROUP_ID \
    --env NO_AT_BRIDGE=1 \
    --env DISPLAY=$DISPLAY \
    --workdir=$(pwd) \
    --volume=/tmp/.X11-unix:/tmp/.X11-unix \
    --volume="/etc/group:/etc/group:ro" \
    --volume="/etc/passwd:/etc/passwd:ro" \
    --volume="/etc/shadow:/etc/shadow:ro" \
    --volume="/home/$USER:/home/$USER:rw" \
    ghcr.io/inti-cmnb/$image $cmd

if [[ "$added_access" == "true" ]]; then
    # Revert back to original xhost access control state
    echo "Reverting xhost to original state..."
    # Remove the added access for local:docker
    xhost -$allow_to
fi
