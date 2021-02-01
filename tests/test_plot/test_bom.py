"""
Tests of KiBoM BoM files

The bom.sch has R1, R2 and C1
We test:
- HTML and CSV

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
from kibot.misc import (BOM_ERROR)

BOM_DIR = 'BoM'


def test_bom_ok(test_dir):
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, 'test_bom_ok', prj, prj, BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # Default format is PRJ_bom_REVISION
    name = os.path.join(BOM_DIR, prj)
    csv = name+'-bom.csv'
    html = name+'_bom__(pp).html'
    ctx.expect_out_file(csv)
    ctx.expect_out_file(html)
    ctx.search_in_file(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    os.remove(os.path.join(ctx.get_board_dir(), 'bom.ini'))
    ctx.clean_up()


def test_bom_fail(test_dir):
    ctx = context.TestContext(test_dir, 'test_bom_fail', 'bom_no_xml', 'bom', BOM_DIR)
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_bom_cfg_1(test_dir):
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, 'test_bom_cfg_1', prj, 'bom_cfg', BOM_DIR)
    ctx.run()
    name = os.path.join(BOM_DIR, prj)
    csv = name+'-bom.csv'
    ctx.expect_out_file(csv)
    ctx.search_in_file(csv, ['R,R1,100 R_0805_2012Metric ~', 'R,R2,200 R_0805_2012Metric ~', 'C,C1,1uF C_0805_2012Metric ~'])
    ctx.clean_up()


def test_bom_cfg_2(test_dir):
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, 'test_bom_cfg_2', prj, 'bom_cfg2', BOM_DIR)
    ctx.run()
    name = os.path.join(BOM_DIR, prj)
    csv = name+'-bom.csv'
    ctx.expect_out_file(csv)
    ctx.search_in_file(csv, ['R,100 R_0805_2012Metric,R1', 'R,200 R_0805_2012Metric,R2'])
    ctx.search_not_in_file(csv, ['C,1uF C_0805_2012Metric,C1'])
    ctx.clean_up()


def test_bom_cfg_3(test_dir):
    """ Without any column """
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, 'test_bom_cfg_3', prj, 'bom_cfg3', BOM_DIR)
    ctx.run()
    name = os.path.join(BOM_DIR, prj)
    csv = name+'-bom.csv'
    ctx.expect_out_file(csv)
    ctx.search_in_file(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    ctx.clean_up()


def test_bom_cfg_4(test_dir):
    """ Without join """
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'test_bom_cfg_4', prj, 'bom_cfg4', BOM_DIR)
    ctx.run()
    name = os.path.join(BOM_DIR, prj)
    csv = name+'-bom.csv'
    ctx.expect_out_file(csv)
    ctx.search_in_file(csv, ['R,100,R1', 'R,200,R2', 'C,1uF,C1'])
    ctx.clean_up()
