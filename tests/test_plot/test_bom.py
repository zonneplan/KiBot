"""
Tests of KiBoM BoM files

The bom.sch has R1, R2 and C1
We test:
- HTML and CSV

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
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kiplot.misc import (BOM_ERROR)

BOM_DIR = 'BoM'


def test_bom_ok():
    prj = 'bom'
    ctx = context.TestContext('BoM_simple', prj, prj, BOM_DIR)
    ctx.run(no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom.sch')])
    # Check all outputs are there
    # Default format is PRJ_bom_REVISION
    name = os.path.join(BOM_DIR, prj+'_bom_')
    csv = name+'.csv'
    html = name+'_(pp).html'
    ctx.expect_out_file(csv)
    ctx.expect_out_file(html)
    ctx.search_in_file(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    os.remove(os.path.join(ctx.get_board_dir(), 'bom.ini'))
    ctx.clean_up()


def test_bom_fail():
    ctx = context.TestContext('BoM_fail', 'bom_no_xml', 'bom', BOM_DIR)
    ctx.run(BOM_ERROR)
    ctx.clean_up()
