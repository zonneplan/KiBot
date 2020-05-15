"""
Tests of InteractiveHtmlBom BoM files

The bom.sch has R1, R2 and C1
We test:
- HTML

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


def test_ibom():
    prj = 'bom'
    ctx = context.TestContext('BoM_interactive', prj, 'ibom', BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # We us this format: %f_iBoM
    name = os.path.join(BOM_DIR, prj+'_iBoM')
    html = name+'.html'
    ctx.expect_out_file(html)
    ctx.clean_up()
