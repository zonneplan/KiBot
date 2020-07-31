"""
Tests of Internal BoM files

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
from copy import deepcopy
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# from kiplot.misc import (BOM_ERROR)

BOM_DIR = 'BoM'
REF_COLUMN_NAME = 'Reference'  # TODO make the same as KiBoM
QTY_COLUMN_NAME = 'Quantity Per PCB'
KIBOM_TEST_HEAD = ['Component', 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME, 'Datasheet',
                   'config']
KIBOM_TEST_COMPONENTS = ['C1', 'C2', 'C3', 'C4', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R9', 'R10']
KIBOM_TEST_EXCLUDE = ['R6']
KIBOM_TEST_GROUPS = 5


def check_kibom_test_netlist(rows, ref_column, groups, exclude, comps):
    """ Checks the kibom-test.sch expected results """
    # Groups
    assert len(rows) == groups
    logging.debug(str(groups) + " groups OK")
    # Components
    if comps:
        components = []
        for r in rows:
            components.extend(r[ref_column].split(' '))
        assert len(components) == len(comps)
        logging.debug(str(len(comps)) + " components OK")
    # Excluded
    if exclude:
        for ex in exclude:
            assert ex not in components
        logging.debug(str(len(exclude)) + " not fitted OK")
    # All the other components
    if comps:
        for c in comps:
            assert c in components
        logging.debug("list of components OK")


def check_dnc(rows, comp, ref, qty):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[qty] == '1 (DNC)'
            logging.debug(comp + " is DNC OK")
            return


def test_int_bom_simple_csv():
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContext('test_int_bom_simple_csv', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run(no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), prj+'.sch')])
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_html():
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContext('test_int_bom_simple_html', prj, 'int_bom_simple_html', BOM_DIR)
    ctx.run(no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), prj+'.sch')])
    out = prj + '-bom.' + ext
    rows, headers = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    head_no_comp = deepcopy(KIBOM_TEST_HEAD)
    head_no_comp[0] = ''  # HTML numbered column doesn't have a name
    assert headers[0] == head_no_comp
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    qty_column = headers[0].index(QTY_COLUMN_NAME)
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, qty_column)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, KIBOM_TEST_COMPONENTS, KIBOM_TEST_EXCLUDE)
    ctx.clean_up()


def adapt_xml(h):
    h = h.replace(' ', '_')
    h = h.replace('"', '')
    h = h.replace("'", '')
    h = h.replace('#', '_num')
    return h


def test_int_bom_simple_xml():
    prj = 'kibom-test'
    ext = 'xml'
    ctx = context.TestContext('test_int_bom_simple_xml', prj, 'int_bom_simple_xml', BOM_DIR)
    ctx.run(no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), prj+'.sch')])
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_TEST_HEAD:
        if c == 'Component':
            continue
        assert adapt_xml(c) in header, "Missing column "+c
    ref_column = header.index(adapt_xml(REF_COLUMN_NAME))
    qty_column = header.index(adapt_xml(QTY_COLUMN_NAME))
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx():
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContext('test_int_bom_simple_xlsx', prj, 'int_bom_simple_xlsx', BOM_DIR)
    ctx.run(no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), prj+'.sch')])
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xlsx(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()
