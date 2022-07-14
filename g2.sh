#!/bin/sh
# Eeschema tests
pytest -v --durations=0 -m "eeschema" --test_dir=output
# KiCad2Step tests and others
pytest -v --durations=0 -m "slow and (not (pcbnew or eeschema))" --test_dir=output
