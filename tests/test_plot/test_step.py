"""
Tests of Printing Schematic files

We test:
- STEP for bom.kicad_pcb

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context

STEP_DIR = '3D'
#STEP_FILE = 'bom.step'


def test_step_1():
    prj = 'bom'
    ctx = context.TestContext('STEP_1', prj, 'step_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(STEP_DIR, prj+'.step'))
    ctx.clean_up()
