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
import re
import json
import logging
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
from utils.lzstring import LZString
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kibot.misc import (BOM_ERROR)

BOM_DIR = 'BoM'
IBOM_OUT = 'bom-ibom.html'


def check_modules(ctx, fname, expected):
    with open(ctx.get_out_path(os.path.join(BOM_DIR, fname)), 'rt') as f:
        text = f.read()
    m = re.search(r'var pcbdata = JSON.parse\(LZString.decompressFromBase64\("(.*)"\)\)', text, re.MULTILINE)
    assert m, text
    lz = LZString()
    js = lz.decompressFromBase64(m.group(1))
    data = json.loads(js)
    skipped = data['bom']['skipped']
    modules = [m['ref'] for m in data['modules']]
    assert len(modules)-len(skipped) == len(expected)
    logging.debug("{} components OK".format(len(expected)))
    for m in expected:
        assert m in modules
        assert modules.index(m) not in skipped
    logging.debug("List of components OK")


def test_ibom():
    prj = 'bom'
    ctx = context.TestContext('BoM_interactive', prj, 'ibom', BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # We use this format: %f_iBoM
    name = os.path.join(BOM_DIR, prj+'_iBoM')
    html = name+'.html'
    ctx.expect_out_file(html)
    ctx.clean_up()


def test_ibom_no_ops():
    prj = 'bom'
    ctx = context.TestContext('BoM_interactiveNoOps', prj, 'ibom_no_ops', BOM_DIR)
    ctx.run()
    fname = os.path.join(BOM_DIR, IBOM_OUT)
    ctx.expect_out_file(fname)
    check_modules(ctx, IBOM_OUT, ['C1', 'R1', 'R2'])
    ctx.clean_up()


def test_ibom_fail():
    ctx = context.TestContext('BoM_interactiveFail', 'ibom_fail', 'ibom', BOM_DIR)
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


def test_ibom_variant_1():
    prj = 'kibom-variante'
    ctx = context.TestContext('test_ibom_variant_1', prj, 'ibom_variant_1', BOM_DIR)
    ctx.run(extra_debug=True)
    # No variant
    logging.debug("* No variant")
    check_modules(ctx, prj+'-ibom.html', ['R1', 'R2', 'R3'])
    # V1
    logging.debug("* t1_v1 variant")
    check_modules(ctx, prj+'-ibom_(V1).html', ['R1', 'R2'])
    # V2
    logging.debug("* t1_v2 variant")
    check_modules(ctx, prj+'-ibom_(V2).html', ['R1', 'R3'])
    # V3
    logging.debug("* t1_v3 variant")
    check_modules(ctx, prj+'-ibom_V3.html', ['R1', 'R4'])
    # V1,V3
    logging.debug("* `bla bla` variant")
    check_modules(ctx, prj+'-ibom_bla_bla.html', ['R1', 'R4'])
    ctx.clean_up()
