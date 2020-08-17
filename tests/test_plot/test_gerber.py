"""
Tests of Gerber format.
- Simple 2 layers
- Inner layer

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
from kibot.misc import (PLOT_ERROR)


GERBER_DIR = 'gerberdir'


def test_gerber_2layer():
    prj = 'simple_2layer'
    ctx = context.TestContext('Simple_2_layer', prj, prj, GERBER_DIR)
    ctx.run()

    f_cu = ctx.get_gerber_filename('F_Cu')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(ctx.get_gerber_job_filename())

    ctx.expect_gerber_has_apertures(f_cu, [
        r"C,0.200000",
        r"R,2.000000X2.000000",
        r"C,1.000000"])

    # expect a flash for the square pad
    ctx.expect_gerber_flash_at(f_cu, 5, (140, -100))

    ctx.clean_up()


def test_gerber_inner_ok():
    prj = 'good-project'
    ctx = context.TestContext('Gerber_Inner', prj, 'gerber_inner', GERBER_DIR)
    ctx.run()

    ctx.expect_out_file(os.path.join(GERBER_DIR, prj+'_GND_Cu.gbr'))
    ctx.expect_out_file(os.path.join(GERBER_DIR, prj+'_Signal1.gbr'))
    ctx.expect_out_file(os.path.join(GERBER_DIR, 'test-'+prj+'.gbrjob'))
    ctx.clean_up()


def test_gerber_inner_wrong():
    prj = 'good-project'
    ctx = context.TestContext('Gerber_InnerWrong', prj, 'gerber_inner_wrong', GERBER_DIR)
    ctx.run(PLOT_ERROR)
    assert ctx.search_err('is not valid for this board')
    ctx.clean_up()
