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
- Missing SCH
- Missing config
- Wrong config name
- Guess the PCB and YAML
- Guess the PCB and YAML when more than one is present
- Guess the SCH and YAML
- Guess the SCH and YAML when more than one is present
- --list
- Create example
  - with PCB
  - already exists
  - Copying
- Load plugin

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import stat
import sys
import shutil
import logging
from subprocess import call
from glob import glob
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kibot.misc import (EXIT_BAD_ARGS, EXIT_BAD_CONFIG, NO_PCB_FILE, NO_SCH_FILE, EXAMPLE_CFG, WONT_OVERWRITE, CORRUPTED_PCB,
                        PCBDRAW_ERR, WRONG_INSTALL)


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


def test_skip_pre_and_outputs_5():
    prj = 'simple_2layer'
    ctx = context.TestContext('SkipPreAndPos4', prj, 'pre_skip', POS_DIR)
    ctx.run(extra=['-s', 'run_erc,run_drc'])
    assert ctx.search_err('no need to skip')
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
    ctx.run(EXIT_BAD_ARGS, extra=['pos_ascii'])

    assert ctx.search_err('No SCH file found')

    ctx.clean_up()


def test_miss_sch_2():
    prj = 'fail-project'
    ctx = context.TestContext('MissingSCH_2', prj, 'pre_and_position', POS_DIR)
    ctx.run(NO_SCH_FILE, no_board_file=True, extra=['-e', 'bogus', 'pos_ascii'])

    assert ctx.search_err('Schematic file not found')

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
    ctx.run(EXIT_BAD_ARGS, no_board_file=True, extra=['-s', 'run_erc,update_xml', 'pos_ascii'])

    assert ctx.search_err('No PCB file found')

    ctx.clean_up()


def test_miss_yaml():
    prj = 'bom'
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
    """ Test guessing the PCB and config file.
        Only one them is there. """
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
    """ Test guessing the PCB and config file.
        Two of them are there. """
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


def test_auto_pcb_and_cfg_3():
    """ Test guessing the SCH and config file.
        Only one them is there. """
    prj = '3Rs'
    ctx = context.TestContext('GuessSCH_cfg', prj, 'pre_and_position', POS_DIR)

    sch = os.path.basename(ctx.sch_file)
    shutil.copy2(ctx.sch_file, ctx.get_out_path(sch))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))

    ctx.run(extra=['-s', 'all', '-i'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)

    assert ctx.search_err('Using SCH file: '+sch)
    assert ctx.search_err('Using config file: '+yaml_file)

    ctx.clean_up()


def test_auto_pcb_and_cfg_4():
    """ Test guessing the SCH and config file.
        Two SCHs and one PCB.
        The SCH with same name as the PCB should be selected. """
    prj = '3Rs'
    ctx = context.TestContext('GuessSCH_cfg_2', prj, 'pre_and_position', POS_DIR)

    sch = os.path.basename(ctx.sch_file)
    shutil.copy2(ctx.sch_file, ctx.get_out_path(sch))
    shutil.copy2(ctx.sch_file, ctx.get_out_path('b_'+sch))
    brd = os.path.basename(ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(brd))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))

    ctx.run(extra=['-s', 'all', '-i'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)

    assert ctx.search_err('Using '+sch)
    assert ctx.search_err('Using config file: '+yaml_file)

    ctx.clean_up()


def test_auto_pcb_and_cfg_5():
    """ Test guessing the SCH and config file.
        Two SCHs. """
    prj = '3Rs'
    ctx = context.TestContext('GuessSCH_cfg_3', prj, 'pre_and_position', POS_DIR)

    sch = os.path.basename(ctx.sch_file)
    shutil.copy2(ctx.sch_file, ctx.get_out_path(sch))
    shutil.copy2(ctx.sch_file, ctx.get_out_path('b_'+sch))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))

    ctx.run(extra=['-s', 'all', '-i'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)

    assert ctx.search_err('Using (b_)?'+sch)
    assert ctx.search_err('Using config file: '+yaml_file)

    ctx.clean_up()


def test_list():
    ctx = context.TestContext('List', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--list'], no_verbose=True, no_out_dir=True, no_board_file=True)

    assert ctx.search_err('run_erc: True')
    assert ctx.search_err('run_drc: True')
    assert ctx.search_err('update_xml: True')
    assert ctx.search_err(r'Pick and place file.? \(position\) \[position\]')
    assert ctx.search_err(r'Pick and place file.? \(pos_ascii\) \[position\]')

    ctx.clean_up()


def test_help():
    ctx = context.TestContext('Help', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--help'], no_verbose=True, no_out_dir=True, no_yaml_file=True)
    assert ctx.search_out('Usage:')
    assert ctx.search_out('Arguments:')
    assert ctx.search_out('Options:')
    ctx.clean_up()


def test_help_list_outputs():
    ctx = context.TestContext('HelpListOutputs', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--help-list-outputs'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Supported outputs:')
    assert ctx.search_out('Gerber format')
    ctx.clean_up()


def test_help_output():
    ctx = context.TestContext('HelpOutput', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--help-output', 'gerber'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Gerber format')
    assert ctx.search_out('Type: .?gerber.?')
    ctx.clean_up()


def test_help_output_unk():
    ctx = context.TestContext('HelpOutputUnk', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, extra=['--help-output', 'bogus'], no_verbose=True, no_out_dir=True, no_yaml_file=True,
            no_board_file=True)
    assert ctx.search_err('Unknown output type')
    ctx.clean_up()


def test_help_output_plugin_1():
    ctx = context.TestContext('test_help_output_plugin_1', '3Rs', 'pre_and_position', POS_DIR)
    home = os.environ['HOME']
    os.environ['HOME'] = os.path.join(ctx.get_board_dir(), '..')
    logging.debug('HOME='+os.environ['HOME'])
    try:
        ctx.run(extra=['--help-output', 'test'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    finally:
        os.environ['HOME'] = home
    assert ctx.search_out('Test for plugin')
    assert ctx.search_out('Type: .?test.?')
    assert ctx.search_out('nothing')
    assert ctx.search_out('chocolate')
    ctx.clean_up()


def test_help_output_plugin_2():
    ctx = context.TestContext('test_help_output_plugin_2', '3Rs', 'pre_and_position', POS_DIR)
    home = os.environ['HOME']
    os.environ['HOME'] = os.path.join(ctx.get_board_dir(), '..')
    logging.debug('HOME='+os.environ['HOME'])
    try:
        ctx.run(extra=['--help-output', 'test2'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    finally:
        os.environ['HOME'] = home
    assert ctx.search_out('Test for plugin')
    assert ctx.search_out('Type: .?test2.?')
    assert ctx.search_out('todo')
    assert ctx.search_out('frutilla')
    ctx.clean_up()


def test_help_outputs():
    ctx = context.TestContext('HelpOutputs', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--help-outputs'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Gerber format')
    assert ctx.search_out('Type: .?gerber.?')
    ctx.clean_up()


def test_help_preflights():
    ctx = context.TestContext('HelpPreflights', '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(extra=['--help-preflights'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Supported preflight options')
    ctx.clean_up()


def test_example_1():
    """ Example without board """
    ctx = context.TestContext('Example1', '3Rs', 'pre_and_position', '')
    ctx.run(extra=['--example'], no_verbose=True, no_yaml_file=True, no_board_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.clean_up()


def test_example_2():
    """ Example with board """
    ctx = context.TestContext('Example2', 'good-project', 'pre_and_position', '')
    ctx.run(extra=['--example'], no_verbose=True, no_yaml_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.search_in_file(EXAMPLE_CFG, ['layers: all'])
    ctx.clean_up()


def test_example_3():
    """ Overwrite error """
    ctx = context.TestContext('Example3', 'good-project', 'pre_and_position', '')
    ctx.run(extra=['--example'], no_verbose=True, no_yaml_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.run(WONT_OVERWRITE, extra=['--example'], no_verbose=True, no_yaml_file=True)
    ctx.clean_up()


def test_example_4():
    """ Expand copied layers """
    ctx = context.TestContext('Example4', 'good-project', 'pre_and_position', '')
    ctx.run(extra=['--example', '-P'], no_verbose=True, no_yaml_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.search_in_file(EXAMPLE_CFG, ['GND.Cu', 'pen_width: 35.0'])
    ctx.search_not_in_file(EXAMPLE_CFG, ['F.Adhes'])
    ctx.clean_up()


def test_example_5():
    """ Copy setting from PCB """
    ctx = context.TestContext('Example5', 'good-project', 'pre_and_position', '')
    output_dir = os.path.join(ctx.output_dir, 'pp')
    ctx.run(extra=['--example', '-p', '-d', output_dir], no_verbose=True, no_yaml_file=True, no_out_dir=True)
    file = os.path.join('pp', EXAMPLE_CFG)
    assert ctx.expect_out_file(file)
    ctx.search_in_file(file, ['layers: selected', 'pen_width: 35.0'])
    ctx.clean_up()


def test_example_6():
    """ Copy setting but no PCB """
    ctx = context.TestContext('Example6', 'good-project', 'pre_and_position', '')
    ctx.run(EXIT_BAD_ARGS, extra=['--example', '-p'], no_verbose=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_err('no PCB specified')
    ctx.clean_up()


def test_corrupted_pcb():
    prj = 'bom_no_xml'
    ctx = context.TestContext('Corrupted', prj, 'print_pcb', '')
    ctx.run(CORRUPTED_PCB)
    assert ctx.search_err('Error loading PCB file')
    ctx.clean_up()


def test_pcbdraw_fail():
    prj = 'bom'
    ctx = context.TestContext('PcbDrawFail', prj, 'pcbdraw_fail', '')
    ctx.run(PCBDRAW_ERR)
    assert ctx.search_err('Failed to run')
    ctx.clean_up()


def test_import_fail():
    ctx = context.TestContext('test_help_output_plugin_1', '3Rs', 'pre_and_position', POS_DIR)
    # Create a read only cache entry that we should delete
    call(['py3compile', 'kibot/out_any_layer.py'])
    cache_dir = os.path.join('kibot', '__pycache__')
    cache_file = glob(os.path.join(cache_dir, 'out_any_layer.*'))[0]
    os.chmod(cache_file, stat.S_IREAD)
    os.chmod(cache_dir, stat.S_IREAD | stat.S_IEXEC)
    try:
        # Run the command
        ctx.run(WRONG_INSTALL, extra=['--help-list-outputs'], no_out_dir=True, no_yaml_file=True, no_board_file=True)
    finally:
        os.chmod(cache_dir, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        os.remove(cache_file)
    assert ctx.search_err('Wrong installation')
    assert ctx.search_err('Unable to import plug-ins')
    ctx.clean_up()
