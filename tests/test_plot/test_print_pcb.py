"""
Tests of Printing PCB files

We test:
- PDF for bom.kicad_pcb

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

PDF_DIR = 'Layers'
PDF_FILE = 'PCB_Top.pdf'


def test_print_sch():
    prj = 'bom'
    ctx = context.TestContext('PrPCB', prj, 'print_pcb', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(PDF_DIR, PDF_FILE))
    ctx.clean_up()
