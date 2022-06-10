"""
Tests of Postscript format.

For debug information use:
pytest-3 --log-cli-level debug
"""
from . import context
PS_DIR = 'PS'


def test_ps(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'ps', PS_DIR)
    ctx.run()

    f_cu = ctx.get_gerber_filename('F_Cu', '.ps')
    f_fab = ctx.get_gerber_filename('F_Fab', '.ps')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(f_fab)
    ctx.dont_expect_out_file(ctx.get_gerber_job_filename())

    ctx.clean_up()


def test_ps_auto(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'ps_auto', PS_DIR)
    ctx.run()

    f_cu = ctx.get_gerber_filename('F_Cu', '.ps')
    f_fab = ctx.get_gerber_filename('F_Fab', '.ps')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(f_fab)
    ctx.dont_expect_out_file(ctx.get_gerber_job_filename())

    ctx.clean_up()
