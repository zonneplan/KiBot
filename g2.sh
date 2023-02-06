#!/bin/sh
set -e
# Eeschema tests
pytest-3 -v --durations=0 -m "eeschema" --test_dir=output
# KiCad2Step tests and others
pytest-3 -v --durations=0 -m "slow and (not (pcbnew or eeschema))" --log-cli-level debug --test_dir=output
