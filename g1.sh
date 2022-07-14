#!/bin/sh
# Fast tests
pytest -v --durations=0 -m "not slow" -n 2 --test_dir=output
# KiCad2Step tests
pytest -v --durations=0 -m "slow and (not (pcbnew or eeschema))" --test_dir=output
