#!/bin/sh
# Fast tests
pytest-3 -v --durations=0 -m "not slow" -n 2 --test_dir=output
