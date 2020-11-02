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
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context

DRILL_DIR = 'Drill'
positions = {'R1': (105, 35, 'top'), 'R2': (110, 35, 'bottom'), 'R3': (110, 45, 'top')}


def do_3Rs(conf, dir, modern, single=False):
    ctx = context.TestContext(dir, '3Rs', conf, DRILL_DIR)
    ctx.run()
    # Check all outputs are there
    pth_drl = ctx.get_pth_drl_filename()
    npth_drl = ctx.get_npth_drl_filename()
    pth_pdf_drl = ctx.get_pth_pdf_drl_filename()
    npth_pdf_drl = ctx.get_npth_pdf_drl_filename()
    pth_gbr_drl = ctx.get_pth_gbr_drl_filename()
    npth_gbr_drl = ctx.get_npth_gbr_drl_filename()
    report = 'report.rpt'

    if modern:
        pth_drl = pth_drl.replace('PTH', 'PTH_drill')
        npth_drl = npth_drl.replace('PTH', 'PTH_drill')
        pth_gbr_drl = pth_gbr_drl.replace('-drl', '_drill')
        npth_gbr_drl = npth_gbr_drl.replace('-drl', '_drill')
        pth_pdf_drl = pth_pdf_drl.replace('-drl', '_drill')
        npth_pdf_drl = npth_pdf_drl.replace('-drl', '_drill')
        report = '3Rs-drill_report.txt'
        if single:
            pth_drl = pth_drl.replace('PTH_', '')
            npth_drl = npth_drl.replace('NPTH_', '')
            pth_pdf_drl = pth_pdf_drl.replace('PTH_', '')
            npth_pdf_drl = npth_pdf_drl.replace('NPTH_', '')
    elif single:
        pth_drl = pth_drl.replace('-PTH', '')
        npth_drl = npth_drl.replace('-NPTH', '')
        pth_pdf_drl = pth_pdf_drl.replace('-PTH', '')
        npth_pdf_drl = npth_pdf_drl.replace('-NPTH', '')

    ctx.expect_out_file(os.path.join(DRILL_DIR, report))
    ctx.expect_out_file(pth_drl)
    ctx.expect_out_file(npth_drl)
    ctx.expect_out_file(pth_gbr_drl)
    ctx.expect_out_file(npth_gbr_drl)
    ctx.expect_out_file(pth_pdf_drl)
    ctx.expect_out_file(npth_pdf_drl)
    # We have R3 at (110, 45) length is 9 mm on X, drill 1 mm
    ctx.search_in_file(pth_drl, ['X110.0Y-45.0', 'X119.0Y-45.0'])
    ctx.expect_gerber_flash_at(pth_gbr_drl, 6, (110, -45))
    ctx.expect_gerber_has_apertures(pth_gbr_drl, ['C,1.000000'])
    # We have a mounting hole at (120, 29) is 2.1 mm in diameter
    ctx.search_in_file(npth_drl, ['X120.0Y-29.0', 'T.C2.100'])
    ctx.expect_gerber_flash_at(npth_gbr_drl, 6, (120, -29))
    ctx.expect_gerber_has_apertures(npth_gbr_drl, ['C,2.100000'])
    ctx.clean_up()


def test_drill_3Rs():
    do_3Rs('drill', 'test_drill_3Rs', True)


def test_drill_single_3Rs():
    do_3Rs('drill_single', 'test_drill_single_3Rs', True, True)


def test_drill_legacy_3Rs():
    do_3Rs('drill_legacy', 'test_drill_legacy_3Rs', False)


def test_drill_legacy_s_3Rs():
    do_3Rs('drill_legacy_s', 'test_drill_legacy_s_3Rs', False, True)
