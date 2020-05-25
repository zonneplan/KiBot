"""
Tests miscellaneous stuff.

- -s all -i
- -s run_erc,update_xml,run_drc -i
- -s all,run_drc
- -s bogus
- An unknown output type
- -s all and_one_of_two_outs

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
from kiplot.misc import (EXIT_BAD_ARGS, EXIT_BAD_CONFIG)


POS_DIR = 'positiondir'


def test_skip_pre_and_outputs():
    prj = 'simple_2layer'
    ctx = context.TestContext('SkipPreAndPos', prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'all', '-i'])

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Skipping all pre-flight actions')
    assert ctx.search_err('Skipping all outputs')

    ctx.clean_up()


def test_skip_pre_and_outputs_2():
    prj = 'simple_2layer'
    ctx = context.TestContext('SkipPreAndPos2', prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'run_erc,update_xml,run_drc', '-i'])

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Skipping run_erc')
    assert ctx.search_err('Skipping run_drc')
    assert ctx.search_err('Skipping update_xml')
    assert ctx.search_err('Skipping all outputs')

    ctx.clean_up()


def test_skip_pre_and_outputs_3():
    prj = 'simple_2layer'
    ctx = context.TestContext('SkipPreAndPos3', prj, 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, extra=['-s', 'all,run_drc'])

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Use `--skip all`')

    ctx.clean_up()


def test_skip_pre_and_outputs_4():
    prj = 'simple_2layer'
    ctx = context.TestContext('SkipPreAndPos4', prj, 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, extra=['-s', 'bogus'])

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Unknown action to skip: bogus')

    ctx.clean_up()


def test_unknown_out():
    prj = 'simple_2layer'
    ctx = context.TestContext('UnknownOut', prj, 'unknown_out', POS_DIR)
    ctx.run(EXIT_BAD_CONFIG)

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err("Unknown output type 'bogus'")

    ctx.clean_up()


def test_select_output():
    prj = '3Rs'
    ctx = context.TestContext('DoASCIISkipCSV', prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'all', 'pos_ascii'])

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    ctx.expect_out_file(ctx.get_pos_both_filename())
    assert ctx.search_err('Skipping position output')

    ctx.clean_up()
