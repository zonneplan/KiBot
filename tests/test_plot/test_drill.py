"""
Tests of drill files

The 3Rs.kicad_pcb has R1 on top, R2 on bottom and a thru-hole component R3 on top.
We test:
- Separated N/PTH files with DRL, Gerber and PDF map

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

DRILL_DIR = 'Drill'
positions = {'R1': (105, 35, 'top'), 'R2': (110, 35, 'bottom'), 'R3': (110, 45, 'top')}


def expect_position(ctx, file, comp, no_comp=[], inches=False):
    """
    Check if a list of components are or aren't in the file
    """
    # Components that must be found
    texts = []
    for k in comp:
        texts.append('^'+k+r'\s+\S+\s+\S+\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+(\S+)\s*$')
    res = ctx.search_in_file(file, texts)
    for k in comp:
        x, y, side = positions[k]
        if inches:
            x = x/25.4
            y = y/25.4
        matches = res.pop(0)
        assert(abs(float(x) - float(matches[0])) < 0.001)
        assert(abs(float(y) + float(matches[1])) < 0.001)
        assert(side == matches[3])

    # Components that must not be found
    texts = []
    for k in no_comp:
        expr = '^'+k+r'\s+\S+\s+\S+\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+(\S+)\s*$'
        texts.append(expr)
    ctx.search_not_in_file(file, texts)


def test_3Rs_drill():
    ctx = context.TestContext('3Rs_drill', '3Rs', 'drill', DRILL_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(DRILL_DIR, 'report.rpt'))
    pth_drl = ctx.get_pth_drl_filename()
    ctx.expect_out_file(pth_drl)
    npth_drl = ctx.get_npth_drl_filename()
    ctx.expect_out_file(npth_drl)
    pth_gbr_drl = ctx.get_pth_gbr_drl_filename()
    ctx.expect_out_file(pth_gbr_drl)
    npth_gbr_drl = ctx.get_npth_gbr_drl_filename()
    ctx.expect_out_file(npth_gbr_drl)
    pth_pdf_drl = ctx.get_pth_pdf_drl_filename()
    ctx.expect_out_file(pth_pdf_drl)
    npth_pdf_drl = ctx.get_npth_pdf_drl_filename()
    ctx.expect_out_file(npth_pdf_drl)
    # We have R3 at (110, 45) length is 9 mm on X, drill 1 mm
    ctx.search_in_file(pth_drl, ['X110.0Y-45.0', 'X119.0Y-45.0'])
    ctx.expect_gerber_flash_at(pth_gbr_drl, 6, (110, -45))
    ctx.expect_gerber_has_apertures(pth_gbr_drl, ['C,1.000000'])
    # We have a mounting hole at (120, 29) is 2.1 mm in diameter
    ctx.search_in_file(npth_drl, ['X120.0Y-29.0', 'T1C2.100'])
    ctx.expect_gerber_flash_at(npth_gbr_drl, 6, (120, -29))
    ctx.expect_gerber_has_apertures(npth_gbr_drl, ['C,2.100000'])
    ctx.clean_up()
