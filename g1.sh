#!/bin/bash
if [ $KI_RELEASE == "nightly" ]; then
     export KIAUS_USE_NIGHTLY="7.0"
fi
# Fast tests
pytest-3 -v --durations=0 -m "not slow" -n 2 --test_dir=output
