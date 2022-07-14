#!/bin/sh
# Fast tests
pytest -v --durations=0 -m "not slow" -n 2 --test_dir=output
