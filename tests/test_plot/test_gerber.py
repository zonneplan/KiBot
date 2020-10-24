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
ALL_LAYERS = ['B_Adhes',
              'B_CrtYd',
              'B_Cu',
              'B_Fab',
              'B_Mask',
              'B_Paste',
              'B_SilkS',
              'Cmts_User',
              'Dwgs_User',
              'Eco1_User',
              'Eco2_User',
              'Edge_Cuts',
              'F_Adhes',
              'F_CrtYd',
              'F_Cu',
              'F_Fab',
              'F_Mask',
              'F_Paste',
              'F_SilkS',
              'Margin',
              ]


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


def compose_fname(dir, prefix, layer, suffix, ext='gbr'):
    return os.path.join(dir, prefix+'-'+layer+suffix+'.'+ext)


def check_layers_exist(ctx, dir, prefix, layers, suffix):
    for layer in layers:
        ctx.expect_out_file(compose_fname(dir, prefix, layer, suffix))
    ctx.expect_out_file(compose_fname(dir, prefix, 'job', suffix, 'gbrjob'))


def check_components(ctx, dir, prefix, layers, suffix, exclude, include):
    for layer in layers:
        fname = compose_fname(dir, prefix, layer, suffix)
        inc = [r'%TO\.C,{}\*%'.format(v) for v in include]
        ctx.search_in_file(fname, inc)
        exc = [r'%TO\.C,{}\*%'.format(v) for v in exclude]
        ctx.search_not_in_file(fname, exc)


def test_gerber_variant_1():
    prj = 'kibom-variant_3'
    ctx = context.TestContext('test_gerber_variant_1', prj, 'gerber_variant_1', GERBER_DIR)
    ctx.run()
    # R3 is a component added to the PCB, included in all cases
    # variant: default     directory: gerber      components: R1, R2 and R3
    check_layers_exist(ctx, 'gerber', prj, ALL_LAYERS, '')
    check_components(ctx, 'gerber', prj, ['F_Paste', 'F_Adhes'], '', ['C1', 'C2'], ['R1', 'R2', 'R3'])
    # variant: production  directory: production  components: R1, R2, R3 and C2
    check_layers_exist(ctx, 'production', prj, ALL_LAYERS, '_(production)')
    check_components(ctx, 'production', prj, ['F_Paste', 'F_Adhes'], '_(production)', ['C1'], ['R1', 'R2', 'R3', 'C2'])
    # variant: test        directory: test        components: R1, R3 and C2
    check_layers_exist(ctx, 'test', prj, ALL_LAYERS, '_(test)')
    check_components(ctx, 'test', prj, ['F_Paste', 'F_Adhes'], '_(test)', ['R2'], ['C1', 'R1', 'R3', 'C2'])
    ctx.clean_up(keep_project=True)
