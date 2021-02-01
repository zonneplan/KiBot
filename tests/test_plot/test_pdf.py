"""
Tests of PDF format (PCB Plot).

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


PS_DIR = 'PDF'


def test_pdf(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, 'Plot_PDF', prj, 'pdf', PS_DIR)
    ctx.run()
    f_cu = ctx.get_gerber_filename('F_Cu', '.pdf')
    f_silk = ctx.get_gerber_filename('B_Silks', '.pdf')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(f_silk)
    ctx.dont_expect_out_file(ctx.get_gerber_job_filename())
    ctx.clean_up()


def test_pdf_refill(test_dir):
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, 'Plot_PDF_Refill', prj, 'pdf_zone-refill', '')
    ctx.run()
    b_cu = ctx.get_gerber_filename('B_Cu', '.pdf')
    ctx.expect_out_file(b_cu)
    ctx.compare_image(b_cu)
    ctx.clean_up()


def test_pdf_variant_1(test_dir):
    prj = 'kibom-variant_4'
    ctx = context.TestContext(test_dir, 'test_pdf_variant_1', prj, 'pdf_variant_1', '')
    ctx.run()
    fname = prj+'-F_Fab.pdf'
    ctx.expect_out_file(fname)
    ctx.compare_image(fname)
    fname = prj+'-B_Fab.pdf'
    ctx.expect_out_file(fname)
    ctx.compare_image(fname)
    ctx.clean_up()
