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
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context

BOM_DIR = 'BoM'


def test_bom():
    prj = 'bom'
    ctx = context.TestContext('BoM_simple', prj, prj, BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # Default format is PRJ_bom_REVISION
    name = os.path.join(BOM_DIR, prj+'_bom_')
    csv = name+'.csv'
    html = name+'.html'
    ctx.expect_out_file(csv)
    ctx.expect_out_file(html)
    ctx.search_in_file(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    os.remove(os.path.join(ctx.get_board_dir(), 'bom.ini'))
    ctx.clean_up()
