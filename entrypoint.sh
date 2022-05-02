#!/bin/bash

# Script configurations
SCRIPT="KiBot"

# Arguments and their default values
CONFIG=""
BOARD=""
SCHEMA=""
SKIP=""
DIR=""
VARIANT=""
TARGETS=""
QUICKSTART=""

# Exit error code
EXIT_ERROR=1

function msg_example {
    echo -e "example: $SCRIPT -d docs -b example.kicad_pcb -e example.sch -c docs.kibot.yaml"
}

function msg_usage {
    echo -e "usage: $SCRIPT [OPTIONS]... -c <yaml-config-file>"
}

function msg_disclaimer {
    echo -e "This is free software: you are free to change and redistribute it"
    echo -e "There is NO WARRANTY, to the extent permitted by law.\n"
    echo -e "See <https://github.com/INTI-CMNB/KiBot>."
}

function msg_illegal_arg {
    echo -e "$SCRIPT: illegal option $@"
}

function msg_help {
    echo -e "\nOptional control arguments:"
    echo -e "  -c, --config FILE .kibot.yaml config file"
    echo -e "  -d, --dir DIR output path. Default: current dir, will be used as prefix of dir configured in config file"
    echo -e "  -b, --board FILE .kicad_pcb board file. Use __SCAN__ to get the first board file found in current folder."
    echo -e "  -e, --schema FILE .sch schematic file.  Use __SCAN__ to get the first schematic file found in current folder."
    echo -e "  -q, --quick-start YES generate configs and outputs automagically (-b, -e, -s, -V, -c are ignored)."
    echo -e "  -s, --skip Skip preflights, comma separated or 'all'"
    echo -e "  -t, --targets List of targets to generate separated by spaces. To only run preflights use __NONE__."
    echo -e "  -V, --variant Global variant"

    echo -e "\nMiscellaneous:"
    echo -e "  -v, --verbose annotate program execution"
    echo -e "  -h, --help display this message and exit"
}

function msg_more_info {
    echo -e "Try '$SCRIPT --help' for more information."
}

function help {
    msg_usage
    echo ""
    msg_help
    echo ""
    msg_example
    echo ""
    msg_disclaimer
}

function illegal_arg {
    msg_illegal_arg "$@"
    echo ""
    msg_usage
    echo ""
    msg_example
    echo ""
    msg_more_info
}

function usage {
    msg_usage
    echo ""
    msg_more_info
}


function args_process {
    while [ "$1" != "" ];
    do
       case "$1" in
           -c | --config ) shift
               if [ "$1" == "__SCAN__" ]; then
                   CONFIG=""
               else
                   CONFIG="-c $1"
               fi
               ;;
           -b | --board ) shift
               if [ "$1" == "__SCAN__" ]; then
                   BOARD=""
               else
                   BOARD="-b $1"
               fi
               ;;
           -e | --schematic ) shift
               if [ "$1" == "__SCAN__" ]; then
                   SCHEMA=""
               else
                   SCHEMA="-e $1"
               fi
               ;;
           -t | --targets ) shift
               if [ "$1" == "__NONE__" ]; then
                   TARGETS="-i"
               elif [ "$1" == "__ALL__" ]; then
                   TARGETS=""
               else
                   TARGETS="$1"
               fi
               ;;
           -V | --variant ) shift
               if [ "$1" == "__NONE__" ]; then
                   VARIANT=""
               else
                   VARIANT="-g variant=$1"
               fi
               ;;
           -d | --dir) shift
               DIR="-d $1"
               ;;
           -q | --quick-start) shift
               QUICKSTART="$1"
               ;;
           -s | --skip) shift
               if [ "$1" == "__NONE__" ]; then
                   SKIP=""
               else
                   SKIP="-s $1"
               fi
               ;;
           -v | --verbose) shift
               if [ "$1" == "0" ]; then
                   VERBOSE=""
               elif [ "$1" == "1" ]; then
                   VERBOSE="-v"
               elif [ "$1" == "2" ]; then
                   VERBOSE="-vv"
               elif [ "$1" == "3" ]; then
                   VERBOSE="-vvv"
               else
                   VERBOSE="-vvvv"
               fi
               ;;
           -h  | --help )
               help
               exit
               ;;
           *)
               illegal_arg "$@"
               exit $EXIT_ERROR
               ;;
        esac
        shift
    done
}

function run {
    if [ -d .git ]; then
        /usr/bin/kicad-git-filters.py
    fi

    if [ $QUICKSTART == "YES" ]; then
        echo Quick-start options: $DIR $VERBOSE --quick-start
        kibot $DIR $VERBOSE --quick-start
    else
        echo Options: $CONFIG $DIR $BOARD $SCHEMA $SKIP $VERBOSE $VARIANT $TARGETS
        kibot $CONFIG $DIR $BOARD $SCHEMA $SKIP $VERBOSE $VARIANT $TARGETS
    fi
}

function main {
    args_process "$@"

    run
}

# Removes quotes
args=$(xargs <<<"$@")

# Arguments as an array
IFS=' ' read -a args <<< "$args"

# Run main
main "${args[@]}"
