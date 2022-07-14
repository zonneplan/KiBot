#!/bin/sh
# PCBnew tests
pytest -v --durations=0 -m "pcbnew" --test_dir=output
