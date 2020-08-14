"""
Tests SCH errors


For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(prev_dir))
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiplot.misc import CORRUPTED_SCH


def setup_ctx(test, file, error):
    test = 'sch_errors_'+test
    ctx = context.TestContextSCH('test_'+test, file, 'int_bom_simple_csv', None)
    ctx.run(CORRUPTED_SCH)
    ctx.search_err(error)
    ctx.clean_up()


def test_sch_errors_no_signature():
    setup_ctx('no_signature', '3Rs', 'No eeschema signature')


def test_sch_errors_no_eelayer():
    setup_ctx('no_eelayer', 'error_no_eelayer', 'Missing EELAYER')


def test_sch_errors_no_eelayer_end():
    setup_ctx('no_eelayer_end', 'error_no_eelayer_end', 'Missing EELAYER END')


def test_sch_errors_unknown_def():
    setup_ctx('unknown_def', 'error_unknown_def', 'Unknown definition')


def test_sch_errors_eof():
    setup_ctx('eof', 'error_eof', 'Unexpected end of file')


def test_sch_errors_l1():
    setup_ctx('l1', 'error_l1', 'Unexpected end of file')


def test_sch_errors_l2():
    setup_ctx('l2', 'error_l2', 'Unexpected end of file')


def test_sch_errors_l3():
    setup_ctx('l3', 'error_l3', 'Malformed component field')


def test_sch_errors_l4():
    setup_ctx('l4', 'error_l4', 'Missing component field name')


def test_sch_errors_l5():
    setup_ctx('l5', 'error_l5', ['Unknown poligon definition', 'Expected 6 coordinates and got 8 in poligon',
              'Unknown square definition', 'Unknown circle definition', 'Unknown arc definition',
              'Unknown text definition', 'Unknown pin definition', 'Failed to load component definition',
              'Unknown draw element'])


def test_sch_errors_l6():
    setup_ctx('l6', 'error_l6', 'Missing library signature')


def test_sch_errors_l7():
    setup_ctx('l7', 'error_l7', 'Unknown library entry')


def test_sch_errors_l8():
    setup_ctx('l8', 'error_l8', ['Unknown DCM entry', 'Unknown DCM attribute'])


def test_sch_errors_l9():
    setup_ctx('l9', 'error_l9', 'Missing DCM signature')


def test_sch_errors_field():
    setup_ctx('field', 'error_field', 'Malformed component field')


def test_sch_errors_field_name():
    setup_ctx('field_name', 'error_field_name', 'Missing component field name')

