"""
Tests of PDF format (PCB Plot).

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


PS_DIR = 'PDF'


def test_pdf():
    prj = 'simple_2layer'
    ctx = context.TestContext('Plot_PDF', prj, 'pdf', PS_DIR)
    ctx.run()

    f_cu = ctx.get_gerber_filename('F_Cu', '.pdf')
    f_silk = ctx.get_gerber_filename('B_Silks', '.pdf')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(f_silk)
    ctx.dont_expect_out_file(ctx.get_gerber_job_filename())

    ctx.clean_up()


def test_pdf_refill():
    prj = 'zone-refill'
    ctx = context.TestContext('Plot_PDF_Refill', prj, 'pdf_zone-refill', '')
    ctx.run()

    b_cu = ctx.get_gerber_filename('B_Cu', '.pdf')
    ctx.expect_out_file(b_cu)
    ctx.compare_image(b_cu)
