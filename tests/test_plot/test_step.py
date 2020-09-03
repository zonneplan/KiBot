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
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context

STEP_DIR = '3D'
# STEP_FILE = 'bom.step'


def test_step_1():
    prj = 'bom'
    ctx = context.TestContext('STEP_1', prj, 'step_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(STEP_DIR, prj+'-3D.step'))
    ctx.clean_up()


def test_step_2():
    prj = 'bom'
    ctx = context.TestContext('STEP_2', prj, 'step_simple_2', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(STEP_DIR, prj+'-3D.step'))
    ctx.clean_up()


def test_step_3():
    prj = 'bom'
    ctx = context.TestContext('STEP_3', prj, 'step_simple_3', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(STEP_DIR, prj+'.step'))
    ctx.clean_up()


def test_step_variant_1():
    prj = 'kibom-variant_3'
    ctx = context.TestContext('test_step_variant_1', prj, 'step_variant_1', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-3D.step')
    ctx.clean_up()
