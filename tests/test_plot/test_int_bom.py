# -*- coding: utf-8 -*-
"""
Tests of Internal BoM files

- Simple cases for:
  - CSV
  - HTML
  - XML
  - XLSX
- Components units
  - Sort and groups of RLC_sort
- Datasheet as link (HTML and XLSX)
- Digi-Key link (HTML and XLSX)
- Join columns
- ignore_dnf = 0
- html_generate_dnf = 0
- use_alt = 1 (also non contiguous)
- COLUMN_RENAME
  - CSV
  - HTML
  - XML
  - XLSX
- group_connectors = 1/0
- Columns are case insensitive
- component_aliases
- merge_blank_fields
- Don't group components
- Multipart component (not repeated)
- Field collision
- test_regex/exclude_any/include_only
- No XLSX support

Missing:
- Variants
- number_boards

- XLSX colors (for real)

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
from base64 import b64decode
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kiplot.misc import EXIT_BAD_CONFIG

BOM_DIR = 'BoM'
REF_COLUMN_NAME = 'References'
REF_COLUMN_NAME_R = 'Referencias'
QTY_COLUMN_NAME = 'Quantity Per PCB'
COMP_COLUMN_NAME = 'Row'
COMP_COLUMN_NAME_R = 'Renglón'
DATASHEET_COLUMN_NAME = 'Datasheet'
KIBOM_TEST_HEAD = [COMP_COLUMN_NAME, 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME,
                   DATASHEET_COLUMN_NAME, 'Config']
KIBOM_TEST_HEAD_TOL = [c for c in KIBOM_TEST_HEAD]
KIBOM_TEST_HEAD_TOL.insert(-1, 'Tolerance')
KIBOM_RENAME_HEAD = [COMP_COLUMN_NAME_R, REF_COLUMN_NAME_R, 'Componente', 'Valor', 'Código Digi-Key', 'Cantidad por PCB']
CONN_HEAD = [COMP_COLUMN_NAME, 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME,
             DATASHEET_COLUMN_NAME]
KIBOM_TEST_COMPONENTS = ['C1', 'C2', 'C3', 'C4', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R9', 'R10']
KIBOM_TEST_COMPONENTS_ALT = ['C1-C4', 'R9-R10', 'R7', 'R8', 'R1-R5']
KIBOM_TEST_COMPONENTS_ALT2 = ['C1-C4', 'R9-R10', 'R7', 'R8', 'R1-R2', 'R4-R5', 'R3']
KIBOM_TEST_EXCLUDE = ['R6']
KIBOM_TEST_GROUPS = 5
KIBOM_PRJ_INFO = ['kibom-test', 'default', 'A', '2020-03-12', None]
KIBOM_STATS = [KIBOM_TEST_GROUPS+len(KIBOM_TEST_EXCLUDE),
               len(KIBOM_TEST_COMPONENTS)+len(KIBOM_TEST_EXCLUDE),
               len(KIBOM_TEST_COMPONENTS),
               1,
               len(KIBOM_TEST_COMPONENTS)]
LINK_HEAD = ['References', 'Part', 'Value', 'Quantity Per PCB', 'digikey#', 'digikey_alt#', 'manf#']
LINKS_COMPONENTS = ['J1', 'J2', 'R1']
LINKS_EXCLUDE = ['C1']
LINKS_GROUPS = 2
INFO_ROWS = ['Schematic:', 'Variant:', 'Revision:', 'Date:', 'KiCad Version:']
STATS_ROWS = ['Component Groups:', 'Component Count:', 'Fitted Components:', 'Number of PCBs:', 'Total Components:']
DEF_TITLE = 'KiBot Bill of Materials'


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


def check_dnc(rows, comp, ref, qty, datasheet=None):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[qty] == '1 (DNC)'
            logging.debug(comp + " is DNC OK")
            if datasheet is not None:
                assert row[datasheet].startswith('<a href="')
                logging.debug(comp + " datasheet link OK")
            return


def check_path(rows, comp, ref, sp, val):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[sp] == val
            logging.debug(comp + " sheetpath OK")
            return


def check_head_xlsx(r, info, stats, title=DEF_TITLE):
    rn = 0
    if title:
        # First row is just the title
        assert r[rn][0] == title
        rn += 1
        logging.debug('Title Ok')
    if info:
        info_col = 0
        for i, txt in enumerate(info):
            assert r[rn+i][info_col] == INFO_ROWS[i]
            if txt:
                assert r[rn+i][info_col+1] == txt
        logging.debug('Info block Ok')
    if stats:
        stats_col = 0
        if info:
            stats_col += 2
        for i, txt in enumerate(stats):
            assert r[rn+i][stats_col] == STATS_ROWS[i]
            assert r[rn+i][stats_col+1] == txt, 'index: {} title: {}'.format(i, STATS_ROWS[i])
        logging.debug('Stats block Ok')


def check_head_html(r, info, stats, title, logo):
    if title:
        assert 'title' in r
        assert r['title'] == title
        logging.debug('Title Ok')
    else:
        assert 'title' not in r
        logging.debug('No title Ok')
    if logo:
        assert 'logo' in r
        logging.debug('Logo Ok')
    else:
        assert 'logo' not in r
        logging.debug('No logo Ok')
    if info:
        assert 'info' in r
        for i, tit in enumerate(INFO_ROWS):
            if info[i] is None:
                continue
            key = 'info_'+tit[:-1]
            assert key in r
            assert info[i] == r[key]
        logging.debug('Info block Ok')
    else:
        assert 'info' not in r
        logging.debug('No info block Ok')
    if stats:
        assert 'stats' in r
        for i, tit in enumerate(STATS_ROWS):
            if stats[i] is None:
                continue
            key = 'stats_'+tit[:-1]
            assert key in r
            assert stats[i] == r[key]
        logging.debug('Stats block Ok')
    else:
        assert 'stats' not in r
        logging.debug('No stats block Ok')


def check_csv_info(r, info, stats):
    row = 0
    if info:
        assert r[row][0] == 'Project info:'
        for i, tit in enumerate(INFO_ROWS):
            row += 1
            assert r[row][0] == tit
            if info[i] is not None:
                assert r[row][1] == info[i]
        logging.debug('Info block Ok')
        row += 1
    if stats:
        assert r[row][0] == 'Statistics:'
        for i, tit in enumerate(STATS_ROWS):
            row += 1
            assert r[row][0] == tit
            if stats[i] is not None:
                assert r[row][1] == str(stats[i])
        logging.debug('Stats block Ok')
        row += 1
    assert row == len(r)



def kibom_verif(rows, header, skip_head=False, qty_name=QTY_COLUMN_NAME):
    if not skip_head:
        assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(qty_name)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)


def kibom_setup(test, ext='csv'):
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_'+test, prj, test, BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    return ctx, out


def test_int_bom_simple_csv():
    ctx, out = kibom_setup('int_bom_simple_csv')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file(os.path.join(BOM_DIR, out), [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_csv_no_info():
    """ No PCB info """
    ctx, out = kibom_setup('int_bom_csv_no_info')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, None, KIBOM_STATS)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file(os.path.join(BOM_DIR, out), [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_csv_no_stats():
    """ No Stats """
    ctx, out = kibom_setup('int_bom_csv_no_stats')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, KIBOM_PRJ_INFO, None)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file(os.path.join(BOM_DIR, out), [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_csv_no_extra():
    """ No Stats, no info """
    ctx, out = kibom_setup('int_bom_csv_no_extra')
    rows, header, info = ctx.load_csv(out)
    assert len(info) == 0
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file(os.path.join(BOM_DIR, out), [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_refuse_no_sep():
    ctx, out = kibom_setup('int_bom_refuse_no_sep')
    rows, header, info = ctx.load_csv(out)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file(os.path.join(BOM_DIR, out), ['"'+KIBOM_TEST_HEAD[0]+'","'+KIBOM_TEST_HEAD[1]+'"'])
    ctx.clean_up()


def test_int_bom_simple_txt():
    ctx, out = kibom_setup('int_bom_simple_txt', 'txt')
    rows, header, info = ctx.load_csv(out, delimiter='\t')
    kibom_verif(rows, header)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    # Check all quoted and tab as delimiter
    ctx.search_in_file(os.path.join(BOM_DIR, out), ['"'+KIBOM_TEST_HEAD[0]+'"\t"'+KIBOM_TEST_HEAD[1]+'"'])
    ctx.clean_up()


def simple_html_test(ctx, rows, headers, sh_head, prj, do_title=True, do_logo=True, do_info=True, do_stats=True):
    title = DEF_TITLE if do_title else None
    info = KIBOM_PRJ_INFO if do_info else None
    stats = None
    if do_stats:
        stats = KIBOM_STATS
    check_head_html(sh_head, info, stats, title=title, logo=do_logo)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == KIBOM_TEST_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    qty_column = headers[0].index(QTY_COLUMN_NAME)
    ds_column = headers[0].index(DATASHEET_COLUMN_NAME)
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, qty_column, ds_column)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, KIBOM_TEST_COMPONENTS, KIBOM_TEST_EXCLUDE)
    ctx.clean_up()


def simple_html_setup(name, ret_val=0):
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContextSCH('test_'+name, prj, name, BOM_DIR)
    ctx.run(ret_val)
    out = prj + '-bom.' + ext
    if ret_val == 0:
        return ctx.load_html(out), prj, ctx
    else:
        return (None, None, None), prj, ctx


def test_int_bom_simple_html_1():
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_1')
    simple_html_test(ctx, rows, headers, sh_head, prj)


def test_int_bom_simple_html_2():
    """ No title """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_2')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False)


def test_int_bom_simple_html_3():
    """ No logo """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_3')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_logo=False)


def test_int_bom_simple_html_4():
    """ No title, no logo """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_4')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False)


def test_int_bom_simple_html_5():
    """ No title, no logo, no info """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_5')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False, do_info=False)


def test_int_bom_simple_html_6():
    """ No title, no logo, no info, no stats """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_6')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False, do_info=False, do_stats=False)


def test_int_bom_simple_html_7():
    """ No title, bogus logo, no info, no stats """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_7', EXIT_BAD_CONFIG)
    ctx.search_err(r'Missing logo file')


def test_int_bom_simple_html_8():
    """ No title, custom logo, no info, no stats """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_8')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=True, do_info=False, do_stats=False)
    logo = sh_head['logo']
    assert logo.startswith('data:image/png;base64,')
    image = b64decode(logo[22:])
    with open('docs/images/Ki.png', 'rb') as f:
        ref = f.read()
    assert image == ref
    logging.debug('Image content OK')


def test_int_bom_simple_html_9():
    """ No title, no logo, no info, no stats, custom style """
    (rows, headers, sh_head), prj, ctx = simple_html_setup('int_bom_simple_html_9')
    style = ctx.load_html_style('kibom-test-bom.html')
    with open('tests/data/html_style.css', 'rt') as f:
        ref = f.read()
    assert style[1:] == ref
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False, do_info=False, do_stats=False)


def adapt_xml(h):
    h = h.replace(' ', '_')
    h = h.replace('"', '')
    h = h.replace("'", '')
    h = h.replace('#', '_num')
    return h


def test_int_bom_simple_xml():
    ctx, out = kibom_setup('int_bom_simple_xml', 'xml')
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_TEST_HEAD:
        assert adapt_xml(c) in header, "Missing column "+c
    kibom_verif(rows, header, skip_head=True, qty_name=adapt_xml(QTY_COLUMN_NAME))
    ctx.clean_up()


def simple_xlsx_verify(ctx, prj, dnf=True):
    ext = 'xlsx'
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, KIBOM_PRJ_INFO, KIBOM_STATS)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    rows, header, sh_head = ctx.load_xlsx(out, 2)
    if dnf:
        check_kibom_test_netlist(rows, ref_column, 1, [], KIBOM_TEST_EXCLUDE)
    else:
        assert rows is None
    ctx.clean_up()


def test_int_bom_simple_xlsx_1():
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx', prj, 'int_bom_simple_xlsx', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def get_column(rows, col, split=True):
    components = []
    for r in rows:
        if split:
            components.extend(r[col].split())
        else:
            components.append(r[col])
    return components


def int_bom_sort(locale, dp):
    prj = 'RLC_sort'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_sort_'+locale, prj, 'int_bom_sort_1', BOM_DIR)
    ctx.run(do_locale=locale)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    ref_column = header.index(REF_COLUMN_NAME)
    exp = ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C1', 'C2', 'C3', 'C4', 'C11', 'C12',
           'L2', 'L1', 'L3',
           'R5', 'R16', 'R12', 'R4', 'R9', 'R10', 'R3']
    if dp == ',':
        exp += ['R2', 'R1', 'R8']
    else:
        # 8,2 k is interpreted as 82 k
        exp += ['R1', 'R2', 'R8']
    exp += ['R7', 'R11', 'R14', 'R13', 'R15']
    check_kibom_test_netlist(rows, ref_column, 23, None, exp)
    # Check the sorting
    assert get_column(rows, ref_column) == exp
    # Check normalization
    vals_column = header.index('Value')
    for r in rows:
        if 'C7' in r[ref_column]:
            assert r[vals_column] == '3'+dp+'3 pF'
            logging.debug('C7 == 3'+dp+'3 pF OK')
            break
    ctx.search_err(r'Malformed value: .?10Q.?')
    ctx.search_err(r'Malformed value: .?\.G.?')
    ctx.search_err(r'Malformed value: .?2\.2k2.?')
    ctx.clean_up()


def test_int_bom_sort_1():
    int_bom_sort('es_AR.UTF-8', ',')


def test_int_bom_sort_2():
    int_bom_sort('en_US.UTF-8', '.')


def test_int_bom_sort_3():
    int_bom_sort('xx_XX.UTF-8', '.')


def test_int_bom_datasheet_link():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_datasheet_link', prj, 'int_bom_datasheet_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    part_column = headers[0].index('Part')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
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
    rows, headers, sh_head = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    dk_column = headers[0].index('digikey#')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the digikey link
    parts = get_column(rows[0]+rows[1], dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_links():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_digikey_links', prj, 'int_bom_digikey_links', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    dk_column = headers[0].index('digikey#')
    dk2_column = headers[0].index('digikey_alt#')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the digikey link
    parts = get_column(rows[0]+rows[1], dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows[0]+rows[1], dk2_column, False)
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
    rows, header, info = ctx.load_csv(out)
    assert header == [COMP_COLUMN_NAME, REF_COLUMN_NAME, 'Part', 'Value', 'manf', 'digikey#', QTY_COLUMN_NAME]
    ref_column = header.index(REF_COLUMN_NAME)
    manf_column = header.index('manf')
    value_column = header.index('Value')
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS+1, [], LINKS_EXCLUDE+LINKS_COMPONENTS)
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
    rows, header, info = ctx.load_csv(out)
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
    rows, headers, sh_head = ctx.load_html(out)
    logging.debug(rows)
    # Test we got the normal and DNF tables
    assert len(rows) == 1
    assert len(headers) == 1
    assert headers[0] == KIBOM_TEST_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    qty_column = headers[0].index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_use_alt():
    """ use_alt: true """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_use_alt', prj, 'int_bom_use_alt', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_ALT)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_use_alt_2():
    """ use_alt: true and not merge blank fields, non contiguous """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_use_alt_2', prj, 'int_bom_use_alt_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_ALT2)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_no_number_rows():
    """ Was number_rows: false, now is different """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_no_number_rows', prj, 'int_bom_no_number_rows', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD[1:]
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_column_rename_csv():
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_column_rename_csv', prj, 'int_bom_column_rename_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_RENAME_HEAD
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_html():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_column_rename_html', prj, 'int_bom_column_rename_html', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    assert headers[0] == KIBOM_RENAME_HEAD
    ref_column = headers[0].index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_xml():
    prj = 'links'
    ext = 'xml'
    ctx = context.TestContextSCH('test_int_bom_column_rename_xml', prj, 'int_bom_column_rename_xml', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_RENAME_HEAD:
        assert adapt_xml(c) in header, "Missing column "+c
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_xlsx():
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_column_rename_xlsx', prj, 'int_bom_column_rename_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    assert header == KIBOM_RENAME_HEAD
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_group_connectors():
    """ Default behavior, ignore the 'Value' for connectors """
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_group_connectors', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == CONN_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, [], ['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_int_bom_no_group_connectors():
    """ group_connectors: false """
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_no_group_connectors', prj, 'int_bom_no_group_connectors', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == CONN_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, [], ['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_int_bom_column_sensitive():
    """ Test if the columns list can contain columns in lowercase """
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_column_sensitive', prj, 'int_bom_column_sensitive', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == [REF_COLUMN_NAME.lower(), 'value', 'part', 'description']
    ref_column = header.index(REF_COLUMN_NAME.lower())
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_alias_csv():
    """ Component aliases and merge blank fields """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_alias_csv', prj, 'int_bom_alias_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_alias_nm_csv():
    """ Component aliases and not merge blank fields """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_alias_nm_csv', prj, 'int_bom_alias_nm_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_no_group_csv():
    """ Don't group components """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_no_group_csv', prj, 'int_bom_no_group_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, len(KIBOM_TEST_COMPONENTS), KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_repeat_csv():
    """ Multipart component (not repeated)
        Also DNC in value + Config. """
    prj = 'kibom-test-rep'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_repeat_csv', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2'], ['U1', 'R1'])
    check_dnc(rows, 'R1', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_collision():
    """ Field collision and exclude_any """
    prj = 'kibom-test-3'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_collision', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD_TOL
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.search_err('Field conflict')
    ctx.clean_up()


def test_int_bom_exclude_any():
    """ Field collision and exclude_any """
    prj = 'kibom-test-3'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_exclude_any', prj, 'int_bom_exclude_any', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD_TOL
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS+['X1'])
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.search_err('Field conflict')
    ctx.clean_up()


def test_int_bom_include_only():
    """ Include only (0805 components) """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_include_only', prj, 'int_bom_include_only', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 3, KIBOM_TEST_EXCLUDE, ['R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8'])
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_no_test_regex():
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_simple_csv', prj, 'int_bom_no_include_only', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_sub_sheet_alt():
    """ Test for 1 sub sheet used twice.
        Also stress the v5 loader.
        Also tests sheet path and no grouping with multi-part components """
    prj = 'test_v5'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_sub_sheet_alt', prj, 'int_bom_sheet_path', BOM_DIR)
    ctx.run()  # extra_debug=True
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD[:-1] + ['Sheetpath']
    ref_column = header.index(REF_COLUMN_NAME)
    sp_column = header.index('Sheetpath')
    check_kibom_test_netlist(rows, ref_column, 6, [], ['C1', 'L1', 'R1', 'R2', 'U1', 'U2'])
    check_path(rows, 'U1', ref_column, sp_column, '/Sub Sheet')
    check_path(rows, 'U2', ref_column, sp_column, '/Sub Sheet 2')
    ctx.clean_up()


def test_int_bom_simple_xlsx_2():
    """ No title """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_2', prj, 'int_bom_simple_xlsx_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, KIBOM_PRJ_INFO, KIBOM_STATS, title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_3():
    """ No logo """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_3', prj, 'int_bom_simple_xlsx_3', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_4():
    """ No title, no logo """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_4', prj, 'int_bom_simple_xlsx_4', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, KIBOM_PRJ_INFO, KIBOM_STATS, title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_5():
    """ No title, no logo, no info """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_5', prj, 'int_bom_simple_xlsx_5', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, None, KIBOM_STATS, title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_6():
    """ No title, no logo, no info, no stats """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_6', prj, 'int_bom_simple_xlsx_6', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    assert len(sh_head) == 0
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_7():
    """ Logo from file, no colors (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_7', prj, 'int_bom_simple_xlsx_7', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_8():
    """ Style green (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_8', prj, 'int_bom_simple_xlsx_8', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_9():
    """ Style red (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_9', prj, 'int_bom_simple_xlsx_9', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_a():
    """ No DNF """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_a', prj, 'int_bom_simple_xlsx_a', BOM_DIR)
    simple_xlsx_verify(ctx, prj, False)


def test_int_bom_datasheet_link_xlsx():
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_datasheet_link_xlsx', prj, 'int_bom_datasheet_link_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_xlsx(out)
    assert headers == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers.index(REF_COLUMN_NAME)
    part_column = headers.index('Part')
    # Check the normal table
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    rows2, headers, sh_head = ctx.load_xlsx(out, 2)
    assert headers == LINK_HEAD
    # Check the DNF table
    check_kibom_test_netlist(rows2, ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows+rows2, part_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'pdf' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_link_xlsx():
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_digikey_link_xlsx', prj, 'int_bom_digikey_link_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_xlsx(out)
    assert headers == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers.index(REF_COLUMN_NAME)
    dk_column = headers.index('digikey#')
    # Check the normal table
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    rows2, headers, sh_head = ctx.load_xlsx(out, 2)
    assert headers == LINK_HEAD
    # Check the DNF table
    check_kibom_test_netlist(rows2, ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows+rows2, dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_links_xlsx():
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_digikey_links_xlsx', prj, 'int_bom_digikey_links_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_xlsx(out)
    assert headers == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers.index(REF_COLUMN_NAME)
    dk_column = headers.index('digikey#')
    dk2_column = headers.index('digikey_alt#')
    # Check the normal table
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    rows2, headers, sh_head = ctx.load_xlsx(out, 2)
    assert headers == LINK_HEAD
    # Check the DNF table
    check_kibom_test_netlist(rows2, ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows+rows2, dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows+rows2, dk2_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_no_xlsx_support():
    ctx = context.TestContextSCH('test_int_bom_no_xlsx_support', 'links', 'int_bom_digikey_links_xlsx', BOM_DIR)
    cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/force_xlsx_error.py')]
    ctx.do_run(cmd)
    ctx.search_err('Python xlsxwriter module not installed')
    ctx.search_err('writing XLSX output')
