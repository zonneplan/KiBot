#!/usr/bin/python3
import os
import sys
# Setup the path to load local kibot module
cur_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(os.path.dirname(cur_dir))
if sys.path[0] != prev_dir:
    try:
        sys.path.remove(prev_dir)
    except ValueError:
        pass
    sys.path.insert(0, prev_dir)
if len(sys.argv) > 1 and sys.argv[1] == 'fake':
    fake_dir = os.path.join(cur_dir, 'fake_pcbnew')
    if fake_dir not in sys.path:
        sys.path.insert(0, fake_dir)
else:
    # Force the pcbnew module load to fail
    sys.modules['pcbnew'] = None
# Import the module to test
# Avoid the insertion of the nightly path
os.environ['KIAUS_USE_NIGHTLY'] = ''
from kibot.__main__ import detect_kicad
detect_kicad()
