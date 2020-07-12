"""
Tests of position file

The 3Rs.kicad_pcb has R1 on top, R2 on bottom and a thru-hole component R3 on top.
We test (both CSV and ASCII):
- Separated files, mm, only SMD
- Unified file, mm, only SMD
- Unified file, mm, not only SMD
- Separated files, inches, only SMD
- Also test a case:
  - without 'comment' field
  - with coloured logs
  - in quiet mode
  - compressed YAML file

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

POS_DIR = 'positiondir'
positions = {'R1': (105, 35, 'top'), 'R2': (110, 35, 'bottom'), 'R3': (110, 45, 'top')}
CSV_EXPR = r'^"%s",[^,]+,[^,]+,"([-\d\.]+)","([-\d\.]+)","([-\d\.]+)","(\S+)"$'
ASCII_EXPR = r'^%s\s+\S+\s+\S+\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+(\S+)\s*$'


def expect_position(ctx, file, comp, no_comp=[], inches=False, csv=False):
    """
    Check if a list of components are or aren't in the file
    """
    # Components that must be found
    texts = []
    for k in comp:
        if csv:
            texts.append(CSV_EXPR % k)
        else:
            texts.append(ASCII_EXPR % k)
    res = ctx.search_in_file(file, texts)
    for k in comp:
        x, y, side = positions[k]
        if inches:
            x = x/25.4
            y = y/25.4
        matches = res.pop(0)
        assert(abs(float(x) - float(matches[0])) < 0.001)
        assert(abs(float(y) + float(matches[1])) < 0.001)
        assert(side == matches[3])

    # Components that must not be found
    texts = []
    for k in no_comp:
        if csv:
            expr = CSV_EXPR % k
        else:
            expr = ASCII_EXPR % k
        texts.append(expr)
    ctx.search_not_in_file(file, texts)


def test_3Rs_position():
    ctx = context.TestContext('3Rs_position', '3Rs', 'simple_position', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_filename()
    pos_bot = ctx.get_pos_bot_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'])
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'])
    ctx.clean_up()


def test_3Rs_position_unified():
    ctx = context.TestContext('3Rs_position_unified', '3Rs', 'simple_position_unified', POS_DIR)
    ctx.run()
    expect_position(ctx, ctx.get_pos_both_filename(), ['R1', 'R2'], ['R3'])
    ctx.clean_up()


def test_3Rs_position_unified_th():
    ctx = context.TestContext('3Rs_position_unified_th', '3Rs', 'simple_position_unified_th', POS_DIR)
    ctx.run()
    expect_position(ctx, os.path.join(POS_DIR, ctx.board_name+'-position.pos'), ['R1', 'R2', 'R3'])
    ctx.clean_up()


def test_3Rs_position_inches():
    ctx = context.TestContext('3Rs_position_inches', '3Rs', 'simple_position_inches', POS_DIR)
    ctx.run()
    pos_top = ctx.get_pos_top_filename()
    pos_bot = ctx.get_pos_bot_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], True)
    ctx.clean_up()


def test_3Rs_position_csv():
    """ Also test a case without comment and color logs """
    ctx = context.TestContext('3Rs_position_csv', '3Rs', 'simple_position_csv', POS_DIR)
    ctx.run(use_a_tty=True)
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], csv=True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], csv=True)
    assert ctx.search_err(r"\[36;1mDEBUG:") is not None
    ctx.clean_up()


def test_3Rs_position_unified_csv():
    """ Also test the quiet mode """
    ctx = context.TestContext('3Rs_position_unified_csv', '3Rs', 'simple_position_unified_csv', POS_DIR)
    ctx.run(no_verbose=True, extra=['-q'])
    expect_position(ctx, ctx.get_pos_both_csv_filename(), ['R1', 'R2'], ['R3'], csv=True)
    assert os.path.getsize(ctx.get_out_path('error.txt')) == 0
    ctx.clean_up()


def test_3Rs_position_unified_th_csv():
    ctx = context.TestContext('3Rs_position_unified_th_csv', '3Rs', 'simple_position_unified_th_csv', POS_DIR)
    ctx.run()
    expect_position(ctx, ctx.get_pos_both_csv_filename(), ['R1', 'R2', 'R3'], csv=True)
    ctx.clean_up()


def test_3Rs_position_inches_csv():
    """ Also test a compressed configuration YAML file """
    ctx = context.TestContext('3Rs_position_inches_csv', '3Rs', 'simple_position_inches_csv', POS_DIR, yaml_compressed=True)
    ctx.run()
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    expect_position(ctx, pos_top, ['R1'], ['R2', 'R3'], inches=True, csv=True)
    expect_position(ctx, pos_bot, ['R2'], ['R1', 'R3'], inches=True, csv=True)
    ctx.clean_up()
