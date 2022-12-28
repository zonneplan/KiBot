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
from . import context

DRILL_DIR = 'Drill'
positions = {'R1': (105, 35, 'top'), 'R2': (110, 35, 'bottom'), 'R3': (110, 45, 'top')}


def do_3Rs(test_dir, conf, modern, single=False):
    ctx = context.TestContext(test_dir, '3Rs_bv', conf, DRILL_DIR, test_name=sys._getframe(1).f_code.co_name)
    ctx.run()
    # Check all outputs are there
    pth_drl = ctx.get_pth_drl_filename()
    npth_drl = ctx.get_npth_drl_filename()
    f1_drl = ctx.get_f1_drl_filename()
    i12_drl = ctx.get_12_drl_filename()
    pth_pdf_drl = ctx.get_pth_pdf_drl_filename()
    npth_pdf_drl = ctx.get_npth_pdf_drl_filename()
    f1_pdf_drl = ctx.get_f1_pdf_drl_filename()
    i12_pdf_drl = ctx.get_12_pdf_drl_filename()
    pth_gbr_drl = ctx.get_pth_gbr_drl_filename()
    npth_gbr_drl = ctx.get_npth_gbr_drl_filename()
    f1_gbr_drl = ctx.get_f1_gbr_drl_filename()
    i12_gbr_drl = ctx.get_12_gbr_drl_filename()
    report = 'report.rpt'

    if modern:
        pth_drl = pth_drl.replace('PTH', 'PTH_drill')
        npth_drl = npth_drl.replace('PTH', 'PTH_drill')
        f1_drl = f1_drl.replace('front-in1', 'front-in1_drill')
        i12_drl = i12_drl.replace('in1-in2', 'in1-in2_drill')
        pth_gbr_drl = pth_gbr_drl.replace('-drl', '_drill')
        npth_gbr_drl = npth_gbr_drl.replace('-drl', '_drill')
        f1_gbr_drl = f1_gbr_drl.replace('-drl', '_drill')
        i12_gbr_drl = i12_gbr_drl.replace('-drl', '_drill')
        pth_pdf_drl = pth_pdf_drl.replace('-drl', '_drill')
        npth_pdf_drl = npth_pdf_drl.replace('-drl', '_drill')
        f1_pdf_drl = f1_pdf_drl.replace('-drl', '_drill')
        i12_pdf_drl = i12_pdf_drl.replace('-drl', '_drill')
        report = '3Rs_bv-drill_report.txt'
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
    ctx.expect_out_file(f1_drl)
    ctx.expect_out_file(i12_drl)
    ctx.expect_out_file(pth_gbr_drl)
    ctx.expect_out_file(npth_gbr_drl)
    ctx.expect_out_file(f1_gbr_drl)
    ctx.expect_out_file(i12_gbr_drl)
    ctx.expect_out_file(pth_pdf_drl)
    ctx.expect_out_file(npth_pdf_drl)
    ctx.expect_out_file(f1_pdf_drl)
    ctx.expect_out_file(i12_pdf_drl)
    # We have R3 at (110, 45) length is 9 mm on X, drill 1 mm
    ctx.search_in_file(pth_drl, ['X110.0Y-45.0', 'X119.0Y-45.0'])
    ctx.expect_gerber_flash_at(pth_gbr_drl, 6, (110, -45))
    ctx.expect_gerber_has_apertures(pth_gbr_drl, ['C,1.000000'])
    # We have a mounting hole at (120, 29) is 2.1 mm in diameter
    ctx.search_in_file(npth_drl, ['X120.0Y-29.0', 'T.C2.100'])
    ctx.expect_gerber_flash_at(npth_gbr_drl, 6, (120, -29))
    ctx.expect_gerber_has_apertures(npth_gbr_drl, ['C,2.100000'])
    ctx.clean_up()


def test_drill_3Rs(test_dir):
    do_3Rs(test_dir, 'drill', True)


def test_drill_single_3Rs(test_dir):
    do_3Rs(test_dir, 'drill_single', True, True)


def test_drill_legacy_3Rs(test_dir):
    do_3Rs(test_dir, 'drill_legacy', False)


def test_drill_legacy_s_3Rs(test_dir):
    do_3Rs(test_dir, 'drill_legacy_s', False, True)


def test_drill_sub_pcb_bp(test_dir):
    """ Test a multiboard example """
    prj = 'batteryPack'
    ctx = context.TestContext(test_dir, prj, 'drill_sub_pcb', 'Drill')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-drill_connector.drl'
    # ctx.search_in_file_d(fname, ['X29.75Y-28.09', 'T3C3.200']) KiKit
    ctx.search_in_file_d(fname, ['X137.5Y-102.0', 'T3C3.200'])  # Currently us
    ctx.search_not_in_file_d(fname, ['X189.0Y-59.0', 'T1C0.400'])
    ctx.clean_up(keep_project=True)
