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
IBOM_OUT = 'ibom.html'


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


def test_ibom_no_ops():
    prj = 'bom'
    ctx = context.TestContext('BoM_interactiveNoOps', prj, 'ibom_no_ops', BOM_DIR)
    ctx.run()
    ctx.expect_out_file(os.path.join(BOM_DIR, IBOM_OUT))
    ctx.clean_up()


def test_ibom_fail():
    ctx = context.TestContext('BoM_interactiveFail', 'bom_no_xml', 'ibom', BOM_DIR)
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_ibom_all_ops():
    prj = 'bom'
    ctx = context.TestContext('BoM_interactiveAll', prj, 'ibom_all_ops', BOM_DIR)
    ctx.run()
    out = os.path.join(BOM_DIR, IBOM_OUT)
    ctx.expect_out_file(out)
    # These options are transferred as defaults:
    ctx.search_in_file(out, [r'"dark_mode": true',
                             r'"show_pads": false',
                             r'"show_fabrication": true',
                             r'"show_silkscreen": false',
                             r'"highlight_pin1": true',
                             r'"redraw_on_drag": false',
                             r'"board_rotation": 18.0',  # 90/5
                             r'"checkboxes": "Sourced,Placed,Bogus"',
                             r'"bom_view": "top-bottom"',
                             r'"layer_view": "B"',
                             r'"extra_fields": \["EF"\]'])
    ctx.clean_up()
