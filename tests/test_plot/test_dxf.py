"""
Tests of DXF format.

For debug information use:
pytest-3 --log-cli-level debug
"""
from . import context
PS_DIR = 'DXF'


def test_dxf(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'dxf', PS_DIR)
    ctx.run()
    ctx.expect_out_file(ctx.get_gerber_filename('F_Cu', '.dxf'))
    ctx.expect_out_file(ctx.get_gerber_filename('F_Fab', '.dxf'))
    ctx.dont_expect_out_file(ctx.get_gerber_job_filename())
    ctx.clean_up()
