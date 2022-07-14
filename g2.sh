#!/bin/sh
# Eeschema tests
pytest -v --durations=0 -m "eeschema" --test_dir=output
