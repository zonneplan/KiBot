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
from kibot.mcpy import activate  # noqa: F401
from kibot.out_pcbdraw import PcbDrawOptions

OUT_DIR = 'PcbDraw'
cov = coverage.Coverage()


def test_pcbdraw_3Rs():
    prj = '3Rs'
    ctx = context.TestContext(OUT_DIR, prj, 'pcbdraw', OUT_DIR)
    ctx.run()
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-top.svg'))
    ctx.expect_out_file(os.path.join(OUT_DIR, prj+'-bottom.svg'))
    ctx.clean_up()


def test_pcbdraw_simple():
    prj = 'bom'
    ctx = context.TestContext(OUT_DIR+'_simple', prj, 'pcbdraw_simple', OUT_DIR)
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
        cov.load()
        cov.start()
        o.run('', None)
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
        cov.load()
        cov.start()
        o.run('', None)
        cov.stop()
        cov.save()
        assert 'using unreliable PNG/JPG' in caplog.text, caplog.text
        assert 'imagemagick' in caplog.text, caplog.text
