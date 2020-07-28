"""
Tests of Printing Schematic files

We test:
- PDF for bom.sch

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kiplot.misc import (PDF_SCH_PRINT)
# Utils import
from utils import context

PDF_DIR = ''
PDF_FILE = 'Schematic.pdf'


def test_print_sch_ok():
    prj = 'bom_no_xml'  # bom has meta data, here we test no meta-data
    ctx = context.TestContext('PrSCH', prj, 'print_sch', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(PDF_FILE)
    ctx.clean_up()


def test_print_sch_fail():
    prj = '3Rs'
    ctx = context.TestContext('PrSCHFail', prj, 'print_sch', PDF_DIR)
    ctx.run(PDF_SCH_PRINT, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'print_err.sch')])
    ctx.clean_up()
