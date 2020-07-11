"""
Tests for PcbDraw.

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


OUT_DIR = 'PcbDraw'


def test_pcbdraw_3Rs():
    prj = '3Rs'
    ctx = context.TestContext(OUT_DIR, prj, 'pcbdraw', OUT_DIR)
    ctx.run()
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-top.svg'))
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-bottom.svg'))
    ctx.clean_up()


def test_pcbdraw_simple():
    prj = 'bom'
    ctx = context.TestContext(OUT_DIR+'_simple', prj, 'pcbdraw_simple', OUT_DIR)
    ctx.run()
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-top.svg'))
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-bottom.svg'))
    ctx.clean_up()
