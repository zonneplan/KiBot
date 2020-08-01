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
REF_COLUMN_NAME = 'References'
QTY_COLUMN_NAME = 'Quantity Per PCB'
COMP_COLUMN_NAME = 'Component'
KIBOM_TEST_HEAD = [COMP_COLUMN_NAME , 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME, 'Datasheet',
                   'Config']
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
    ctx = context.TestContextSCH('test_int_bom_simple_csv', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
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
    ctx = context.TestContextSCH('test_int_bom_simple_html', prj, 'int_bom_simple_html', BOM_DIR)
    ctx.run()
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
    ctx = context.TestContextSCH('test_int_bom_simple_xml', prj, 'int_bom_simple_xml', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_TEST_HEAD:
        if c == COMP_COLUMN_NAME:
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
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx', prj, 'int_bom_simple_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xlsx(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def get_column(rows, col, split=True):
    components = []
    for r in rows:
        if split:
            components.extend(r[col].split())
        else:
            components.append(r[col])
    return components


def test_int_bom_sort_1():
    prj = 'RLC_sort'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_sort_1', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    ref_column = header.index(REF_COLUMN_NAME)
    exp = ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C1', 'C2', 'C3', 'C4', 'C11', 'C12',
           'R5', 'R4', 'R9', 'R10', 'R3', 'R2', 'R1', 'R8', 'R7']
    check_kibom_test_netlist(rows, ref_column, 14, None, exp)
    # Check the sorting
    assert get_column(rows, ref_column) == exp
    ctx.clean_up()


def test_int_bom_datasheet_link():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_datasheet_link', prj, 'int_bom_datasheet_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    head_no_comp = deepcopy(KIBOM_TEST_HEAD)
    assert headers[0] == ['', 'References', 'Part', 'Value', 'Quantity Per PCB', 'digikey#', 'manf#']
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    part_column = headers[0].index('Part')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, 2, ['C1'], ['J1', 'J2','R1'])
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, ['J1', 'J2','R1'], ['C1'])
    # Check the datasheet link
    parts = get_column(rows[0]+rows[1], part_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'pdf' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_link():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_digikey_link', prj, 'int_bom_digikey_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    head_no_comp = deepcopy(KIBOM_TEST_HEAD)
    assert headers[0] == ['', 'References', 'Part', 'Value', 'Quantity Per PCB', 'digikey#', 'manf#']
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    dk_column = headers[0].index('digikey#')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, 2, ['C1'], ['J1', 'J2','R1'])
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, ['J1', 'J2','R1'], ['C1'])
    # Check the digikey link
    parts = get_column(rows[0]+rows[1], dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_join_1():
    prj = 'join'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_join_1', prj, 'int_bom_join_1', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == [COMP_COLUMN_NAME, REF_COLUMN_NAME, 'Part', 'Value', 'manf', 'digikey#', QTY_COLUMN_NAME]
    ref_column = header.index(REF_COLUMN_NAME)
    manf_column = header.index('manf')
    value_column = header.index('Value')
    check_kibom_test_netlist(rows, ref_column, 3, [], ['C1', 'J1', 'J2', 'R1'])
    assert rows[0][ref_column] == 'C1'
    assert rows[0][value_column] == '1nF 10% 50V'
    assert rows[0][manf_column] == 'KEMET C0805C102K5RACTU'
    assert rows[1][ref_column] == 'J1 J2'
    assert rows[1][value_column] == 'Molex KK'
    assert rows[1][manf_column] == 'Molex 0022232021'
    assert rows[2][ref_column] == 'R1'
    assert rows[2][value_column] == '1k 5%'
    assert rows[2][manf_column] == 'Bourns CR0805-JW-102ELF'
    ctx.clean_up()


def test_int_include_dnf():
    """ ignore_dnf: false """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_include_dnf', prj, 'int_bom_include_dnf', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, [], KIBOM_TEST_COMPONENTS+KIBOM_TEST_EXCLUDE)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_html_generate_dnf():
    """ html_generate_dnf: false """
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_html_generate_dnf', prj, 'int_bom_html_generate_dnf', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers = ctx.load_html(out)
    logging.debug(rows)
    # Test we got the normal and DNF tables
    assert len(rows) == 1
    assert len(headers) == 1
    # Test both tables has the same headings and they are the expected
    head_no_comp = deepcopy(KIBOM_TEST_HEAD)
    head_no_comp[0] = ''  # HTML numbered column doesn't have a name
    assert headers[0] == head_no_comp
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    qty_column = headers[0].index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, qty_column)
    ctx.clean_up()

