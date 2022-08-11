#!/bin/sh
# PCBnew tests
pytest-3 -v --durations=0 -m "pcbnew" --test_dir=output
