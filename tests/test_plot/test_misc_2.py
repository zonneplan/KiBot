import os
import sys
import pytest
import coverage
import logging
from subprocess import CalledProcessError
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kibot.out_base import BaseOutput
from kibot.gs import GS
from kibot.kiplot import load_actions
from kibot.registrable import RegOutput
from kibot.misc import (MISSING_TOOL, WRONG_INSTALL)


cov = coverage.Coverage()
mocked_check_output_FNF = True


# Important note:
# - We can't load the plug-ins twice, the import fails.
# - Once we patched them using monkey patch the patch isn't reverted unless we load them again.
# For this reason this patch is used for more than one case.
def mocked_check_output(cmd, stderr=None):
    logging.debug('mocked_check_output called')
    if mocked_check_output_FNF:
        raise FileNotFoundError()
    else:
        e = CalledProcessError(10, 'rar')
        e.output = b'THE_ERROR'
        raise e


def run_compress(ctx):
    # Load the plug-ins
    load_actions()
    # Create a compress object with the dummy file as source
    out = RegOutput.get_class_for('compress')()
    out.set_tree({'options': {'format': 'RAR', 'files': [{'source': ctx.get_out_path('*')}]}})
    out.config()
    # Setup the GS output dir, needed for the output path
    GS.out_dir = '.'
    # Start coverage
    cov.load()
    cov.start()
    # Run the compression and catch the error
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        out.run('')
    # Stop coverage
    cov.stop()
    cov.save()
    return pytest_wrapped_e


def test_no_rar(caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = True
    # Create a silly context to get the output path
    ctx = context.TestContext('test_no_rar', 'test_v5', 'empty_zip', '')
    # The file we pretend to compress
    ctx.create_dummy_out_file('Test.txt')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        m.setattr("subprocess.check_output", mocked_check_output)
        pytest_wrapped_e = run_compress(ctx)
    # Check we exited because rar isn't installed
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == MISSING_TOOL
    assert "Missing `rar` command" in caplog.text


def test_rar_fail(caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    # Create a silly context to get the output path
    ctx = context.TestContext('test_no_rar', 'test_v5', 'empty_zip', '')
    # The file we pretend to compress
    ctx.create_dummy_out_file('Test.txt')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        m.setattr("subprocess.check_output", mocked_check_output)
        pytest_wrapped_e = run_compress(ctx)
    # Check we exited because rar isn't installed
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == WRONG_INSTALL
    assert "Failed to invoke rar command, error 10" in caplog.text
    # Not in the docker image ... pytest issue?
    # assert "THE_ERROR" in caplog.text


class NoGetTargets(BaseOutput):
    def __init__(self):
        self.options = True
        self.comment = 'Fake'
        self.name = 'dummy'
        self.type = 'none'
        self._sch_related = True


def test_no_get_targets(caplog):
    test = NoGetTargets()
    test.get_targets('')
    assert "Output 'Fake' (dummy) [none] doesn't implement get_targets(), plese report it" in caplog.text
    # Also check the dependencies fallback
    GS.sch = None
    GS.sch_file = 'fake'
    assert test.get_dependencies() == [GS.sch_file]
