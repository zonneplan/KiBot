"""
Tests of position file

The 3Rs.kicad_pcb has R1 on top, R2 on bottom and a thru-hole component R3 on top.
We test:
- Separated files, mm, only SMD
- Unified file, mm, only SMD
- Unified file, mm, not only SMD
- Separated files, inches, only SMD

For debug information use:
pytest-3 --log-cli-level debug

"""

from . import plotting_test_utils

import os
import mmap
import re
import logging


def expect_file_at(filename):

    assert(os.path.isfile(filename))


def get_pos_top_filename(board_name):
    return board_name + '-top.pos'


def get_pos_bot_filename(board_name):
    return board_name + '-bottom.pos'


def get_pos_both_filename(board_name):
    return board_name + '-both.pos'


def expect_position(pos_data, side, ref, x, y, expected, inches=False):
    """
    Check if a component is or isn't in the file
    """

    # expr = rb'^'+ref.encode()+rb'\s+\S+\s+\S+\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(\S+)$'
    expr = rb'^'+ref.encode()+rb'\s+\S+\s+\S+\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+(\S+)\s*$'

    m = re.search(expr, pos_data, re.MULTILINE)

    if m:
        logging.debug("Position found for " + ref)
    else:
        logging.debug("Position not found for " + ref)

    if expected:
        assert(m)
        if inches:
            x = x/25.4
            y = y/25.4
        assert(abs(float(x) - float(m.group(1))) < 0.001)
        assert(abs(float(y) + float(m.group(2))) < 0.001)
        assert(side == m.group(4).decode())
        # logging.debug(ref+' '+str(x)+' '+str(y)+' -> '+m.group(1).decode()+' '+m.group(2).decode()+' '+m.group(3).decode()+
        # ' '+m.group(4).decode())
    else:
        assert(m is None)


def get_mmapped_data(filename):

    with open(filename) as fo:
        return mmap.mmap(fo.fileno(), 0, access=mmap.ACCESS_READ)


def test_3Rs_position():

    ctx = plotting_test_utils.KiPlotTestContext('3Rs_position')

    ctx.board_name = '3Rs'
    ctx.load_yaml_config_file('simple_position.yaml')

    ctx.do_plot()

    pos_dir = ctx.cfg.resolve_output_dir_for_name('position')

    pos_top = os.path.join(pos_dir, get_pos_top_filename(ctx.board_name))
    pos_bot = os.path.join(pos_dir, get_pos_bot_filename(ctx.board_name))

    expect_file_at(pos_top)
    expect_file_at(pos_bot)

    top = get_mmapped_data(pos_top)
    bot = get_mmapped_data(pos_bot)
    expect_position(top, 'top', 'R1', 105, 35, True)
    expect_position(bot, 'bottom', 'R1', 105, 35, False)
    expect_position(top, 'top', 'R2', 110, 35, False)
    expect_position(bot, 'bottom', 'R2', 110, 35, True)
    expect_position(top, 'top', 'R3', 110, 45, False)
    expect_position(bot, 'bottom', 'R3', 110, 45, False)

    ctx.clean_up()


def test_3Rs_position_unified():

    ctx = plotting_test_utils.KiPlotTestContext('3Rs_position_unified')

    ctx.board_name = '3Rs'
    ctx.load_yaml_config_file('simple_position_unified.yaml')

    ctx.do_plot()

    pos_dir = ctx.cfg.resolve_output_dir_for_name('position')

    pos_both = os.path.join(pos_dir, get_pos_both_filename(ctx.board_name))

    expect_file_at(pos_both)

    both = get_mmapped_data(pos_both)
    expect_position(both, 'top', 'R1', 105, 35, True)
    expect_position(both, 'bottom', 'R2', 110, 35, True)
    expect_position(both, '', 'R3', 110, 45, False)

    ctx.clean_up()


def test_3Rs_position_unified_th():

    ctx = plotting_test_utils.KiPlotTestContext('3Rs_position_unified_th')

    ctx.board_name = '3Rs'
    ctx.load_yaml_config_file('simple_position_unified_th.yaml')

    ctx.do_plot()

    pos_dir = ctx.cfg.resolve_output_dir_for_name('position')

    pos_both = os.path.join(pos_dir, get_pos_both_filename(ctx.board_name))

    expect_file_at(pos_both)

    both = get_mmapped_data(pos_both)
    expect_position(both, 'top', 'R1', 105, 35, True)
    expect_position(both, 'bottom', 'R2', 110, 35, True)
    expect_position(both, 'top', 'R3', 110, 45, True)

    ctx.clean_up()


def test_3Rs_position_inches():

    ctx = plotting_test_utils.KiPlotTestContext('3Rs_position_inches')

    ctx.board_name = '3Rs'
    ctx.load_yaml_config_file('simple_position_inches.yaml')

    ctx.do_plot()

    pos_dir = ctx.cfg.resolve_output_dir_for_name('position')

    pos_top = os.path.join(pos_dir, get_pos_top_filename(ctx.board_name))
    pos_bot = os.path.join(pos_dir, get_pos_bot_filename(ctx.board_name))

    expect_file_at(pos_top)
    expect_file_at(pos_bot)

    top = get_mmapped_data(pos_top)
    bot = get_mmapped_data(pos_bot)
    expect_position(top, 'top', 'R1', 105, 35, True, True)
    expect_position(bot, 'bottom', 'R1', 105, 35, False, True)
    expect_position(top, 'top', 'R2', 110, 35, False, True)
    expect_position(bot, 'bottom', 'R2', 110, 35, True, True)
    expect_position(top, 'top', 'R3', 110, 45, False, True)
    expect_position(bot, 'bottom', 'R3', 110, 45, False, True)

    ctx.clean_up()
