"""
Tests miscellaneous stuff.

- -s all -i
- -s run_erc,update_xml,run_drc -i
- -s all,run_drc
- -s bogus
- An unknown output type
- -s all and_one_of_two_outs
- Missing schematic
- Wrong PCB name
- Missing PCB
- Missing config
- Wrong config name
- Guess the PCB and YAML
- Guess the PCB and YAML when more than one is present
- --list

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
import shutil
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kiplot.misc import (EXIT_BAD_ARGS, EXIT_BAD_CONFIG, NO_SCH_FILE, NO_PCB_FILE)


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
    assert ctx.search_err('Skipping .?run_erc')
    assert ctx.search_err('Skipping .?run_drc')
    assert ctx.search_err('Skipping .?update_xml')
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
    assert ctx.search_err('Unknown preflight .?bogus')

    ctx.clean_up()


def test_unknown_out():
    prj = 'simple_2layer'
    ctx = context.TestContext('UnknownOut', prj, 'unknown_out', POS_DIR)
    ctx.run(EXIT_BAD_CONFIG)

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err("Unknown output type:? .?bogus")

    ctx.clean_up()


def test_select_output():
    prj = '3Rs'
    ctx = context.TestContext('DoASCIISkipCSV', prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'all', 'pos_ascii'])

    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    ctx.expect_out_file(ctx.get_pos_both_filename())
    assert ctx.search_err('Skipping (.*)position(.*) output')

    ctx.clean_up()


def test_miss_sch():
    prj = 'fail-project'
    ctx = context.TestContext('MissingSCH', prj, 'pre_and_position', POS_DIR)
    ctx.run(NO_SCH_FILE, extra=['pos_ascii'])

    assert ctx.search_err('Missing schematic')

    ctx.clean_up()


def test_miss_pcb():
    prj = '3Rs'
    ctx = context.TestContext('MissingPCB', prj, 'pre_and_position', POS_DIR)
    ctx.board_file = 'bogus'
    ctx.run(NO_PCB_FILE, extra=['-s', 'run_erc,update_xml', 'pos_ascii'])

    assert ctx.search_err('Board file not found')

    ctx.clean_up()


def test_miss_pcb_2():
    ctx = context.TestContext('MissingPCB_2', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, no_board_file=True)

    assert ctx.search_err('No PCB file found')

    ctx.clean_up()


def test_miss_yaml():
    prj = '3Rs'
    ctx = context.TestContext('MissingYaml', prj, 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, no_yaml_file=True)

    assert ctx.search_err('No config file')

    ctx.clean_up()


def test_miss_yaml_2():
    prj = '3Rs'
    ctx = context.TestContext('MissingYaml_wrong', prj, 'pre_and_position', POS_DIR)
    ctx.yaml_file = 'bogus'
    ctx.run(EXIT_BAD_ARGS)

    assert ctx.search_err('Plot config file not found: bogus')

    ctx.clean_up()


def test_auto_pcb_and_cfg():
    prj = '3Rs'
    ctx = context.TestContext('GuessPCB_cfg', prj, 'pre_and_position', POS_DIR)

    board_file = os.path.basename(ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(board_file))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))

    ctx.run(extra=['-s', 'all', '-i', 'pos_ascii'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)

    ctx.dont_expect_out_file(ctx.get_pos_both_filename())
    ctx.expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Using PCB file: '+board_file)
    assert ctx.search_err('Using config file: '+yaml_file)

    ctx.clean_up()


def test_auto_pcb_and_cfg_2():
    prj = '3Rs'
    ctx = context.TestContext('GuessPCB_cfg_rep', prj, 'pre_and_position', POS_DIR)

    board_file = os.path.basename(ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(board_file))
    shutil.copy2(ctx.board_file, ctx.get_out_path('b_'+board_file))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))
    shutil.copy2(ctx.yaml_file, ctx.get_out_path('b_'+yaml_file))

    ctx.run(extra=['-s', 'all', '-i', 'pos_ascii'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)

    assert ctx.search_err('WARNING:More than one PCB')
    assert ctx.search_err('WARNING:More than one config')
    m = ctx.search_err('Using (.*).kicad_pcb')
    assert m
    ctx.board_name = m.group(1)

    ctx.dont_expect_out_file(ctx.get_pos_both_filename())
    ctx.expect_out_file(ctx.get_pos_both_csv_filename())

    ctx.clean_up()


def test_list():
    ctx = context.TestContext('List', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--list'])

    assert ctx.search_err('run_erc: True')
    assert ctx.search_err('run_drc: True')
    assert ctx.search_err('update_xml: True')
    assert ctx.search_err(r'Pick and place file.? \(position\) \[position\]')
    assert ctx.search_err(r'Pick and place file.? \(pos_ascii\) \[position\]')

    ctx.clean_up()
