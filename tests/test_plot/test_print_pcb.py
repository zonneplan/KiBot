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
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context

PDF_DIR = 'Layers'
PDF_FILE = 'bom-F_Cu+F_SilkS.pdf'
PDF_FILE_B = 'PCB_Bot.pdf'
PDF_FILE_C = 'PCB_Bot_def.pdf'


def test_print_pcb_simple(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'print_pcb_simple', prj, 'print_pcb', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(os.path.join(PDF_DIR, PDF_FILE))
    ctx.clean_up()


def test_print_pcb_refill_1(test_dir):
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, 'print_pcb_refill', prj, 'print_pcb_zone-refill', '')
    ctx.run()
    ctx.expect_out_file(PDF_FILE_B)
    ctx.compare_image(PDF_FILE_B)
    ctx.clean_up()


def test_print_pcb_refill_2(test_dir):
    """ Using KiCad 6 colors """
    if context.ki5():
        return
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, 'print_pcb_refill', prj, 'print_pcb_zone-refill_def', '')
    ctx.run()
    ctx.expect_out_file(PDF_FILE_B)
    ctx.compare_image(PDF_FILE_B, PDF_FILE_C)
    ctx.clean_up()


def test_print_variant_1(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, 'print_variant_1', prj, 'print_pcb_variant_1', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-F_Fab.pdf'
    ctx.search_err(r'KiCad project file not found', True)
    ctx.expect_out_file(fname)
    ctx.compare_pdf(fname)
    ctx.clean_up(keep_project=True)


def test_print_pcb_options(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'print_pcb_options', prj, 'print_pcb_options', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(PDF_FILE)
    ctx.compare_pdf(PDF_FILE)
    ctx.clean_up()


def test_print_wrong_paste(test_dir):
    prj = 'wrong_paste'
    ctx = context.TestContext(test_dir, 'print_wrong_paste', prj, 'wrong_paste', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    fname = prj+'-F_Fab.pdf'
    ctx.expect_out_file(fname)
    ctx.search_err(r'Pad with solder paste, but no copper')
    ctx.clean_up()
