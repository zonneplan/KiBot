"""
Tests for PcbDraw.

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
import coverage
from shutil import which
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
# One more level for the project
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kibot.mcpyrate import activate  # noqa: F401
from kibot.out_pcbdraw import PcbDrawOptions

OUT_DIR = 'PcbDraw'
cov = coverage.Coverage()


def test_pcbdraw_3Rs(test_dir):
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw', OUT_DIR)
    ctx.run()
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-top.svg'))
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-bottom.svg'))
    ctx.clean_up()


def test_pcbdraw_simple(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_simple', OUT_DIR)
    ctx.run()
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-top.png'))
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-bottom.jpg'))
    ctx.clean_up()


def no_rsvg_convert(name):
    if name == 'rsvg-convert':
        return None
    return which(name)


def no_convert(name):
    if name == 'convert':
        return None
    return which(name)


def no_run(cmd, stderr):
    return b""


def test_pcbdraw_miss_rsvg(caplog, monkeypatch):
    """ Check missing rsvg-convert """
    with monkeypatch.context() as m:
        m.setattr("shutil.which", no_rsvg_convert)
        m.setattr("subprocess.check_output", no_run)
        o = PcbDrawOptions()
        o.style = ''
        o.remap = None
        o.format = 'jpg'
        o.config(None)
        cov.load()
        cov.start()
        o.run('')
        cov.stop()
        cov.save()
        assert 'using unreliable PNG/JPG' in caplog.text, caplog.text
        assert 'librsvg2-bin' in caplog.text, caplog.text


def test_pcbdraw_miss_convert(caplog, monkeypatch):
    """ Check missing convert """
    with monkeypatch.context() as m:
        m.setattr("shutil.which", no_convert)
        m.setattr("subprocess.check_output", no_run)
        o = PcbDrawOptions()
        o.style = ''
        o.remap = None
        o.format = 'jpg'
        o.config(None)
        cov.load()
        cov.start()
        o.run('')
        cov.stop()
        cov.save()
        assert 'using unreliable PNG/JPG' in caplog.text, caplog.text
        assert 'imagemagick' in caplog.text, caplog.text


def test_pcbdraw_variant_1(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_variant_1', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-top.png'
    ctx.expect_out_file(fname)
    # We use 40% because different versions of the tools are generating large differences
    # in the borders. With 40% these differences are removed and we still detect is a
    # components was removed.
    # Expected: R1 and R2 populated
    ctx.compare_image(fname, fuzz='40%')
    ctx.clean_up(keep_project=True)


def test_pcbdraw_variant_2(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_variant_2', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-top-C1.png'
    ctx.expect_out_file(fname)
    # Expected: R1 and R2 populated + C1 manually added
    ctx.compare_image(fname, fuzz='40%')
    ctx.clean_up(keep_project=True)


def test_pcbdraw_variant_3(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_variant_3', '')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-top.png'
    ctx.expect_out_file(fname)
    ctx.compare_image(fname, fuzz='40%')
    assert ctx.search_err("Ambiguous list of components to show .?none.? vs variant/filter")
    ctx.clean_up(keep_project=True)
