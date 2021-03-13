import os
import sys
import re
import pytest
import coverage
import logging
import subprocess
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kibot.layer import Layer
from kibot.pre_base import BasePreFlight
from kibot.out_base import BaseOutput
from kibot.gs import GS
from kibot.kiplot import load_actions, _import, load_board, search_as_plugin, generate_makefile
from kibot.registrable import RegOutput, RegFilter
from kibot.misc import (MISSING_TOOL, WRONG_INSTALL, BOM_ERROR, DRC_ERROR, ERC_ERROR, PDF_PCB_PRINT, CMD_PCBNEW_PRINT_LAYERS,
                        KICAD2STEP_ERR)
from kibot.bom.columnlist import ColumnList
from kibot.bom.units import get_prefix
from kibot.__main__ import detect_kicad
from kibot.kicad.config import KiConf


cov = coverage.Coverage()
mocked_check_output_FNF = True
mocked_check_output_retOK = ''
mocked_call_enabled = False


# Important note:
# - We can't load the plug-ins twice, the import fails.
# - Once we patched them using monkey patch the patch isn't reverted unless we load them again.
# I don't know the real reason, may be related to the way we load plug-ins.
# For this reason this patch is used for more than one case.
def mocked_check_output(cmd, stderr=None):
    logging.debug('mocked_check_output called')
    if mocked_check_output_FNF:
        raise FileNotFoundError()
    else:
        if mocked_check_output_retOK:
            return mocked_check_output_retOK
        e = subprocess.CalledProcessError(10, 'rar')
        e.output = b'THE_ERROR'
        raise e


def mocked_call(cmd):
    if mocked_call_enabled:
        logging.debug('Forcing fail on '+str(cmd))
        return 5
    return subprocess.call(cmd)


def patch_functions(m):
    m.setattr("subprocess.check_output", mocked_check_output)
    m.setattr('kibot.kiplot.exec_with_retry', mocked_call)


def run_compress(ctx, test_import_fail=False):
    with context.cover_it(cov):
        # Load the plug-ins
        load_actions()
        # Create a compress object with the dummy file as source
        out = RegOutput.get_class_for('compress')()
        out.set_tree({'options': {'format': 'RAR', 'files': [{'source': ctx.get_out_path('*')}]}})
        out.config(None)
        # Setup the GS output dir, needed for the output path
        GS.out_dir = '.'
        # Run the compression and catch the error
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            if test_import_fail:
                _import('out_bogus', os.path.abspath(os.path.join(os.path.dirname(__file__), 'fake_plugin/out_bogus.py')))
            else:
                out.run('')
    return pytest_wrapped_e


def test_no_rar(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = True
    # Create a silly context to get the output path
    ctx = context.TestContext(test_dir, 'test_no_rar', 'test_v5', 'empty_zip', '')
    # The file we pretend to compress
    ctx.create_dummy_out_file('Test.txt')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        patch_functions(m)
        pytest_wrapped_e = run_compress(ctx)
    # Check we exited because rar isn't installed
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == MISSING_TOOL
    assert "Missing `rar` command" in caplog.text


def test_rar_fail(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    # Create a silly context to get the output path
    ctx = context.TestContext(test_dir, 'test_no_rar', 'test_v5', 'empty_zip', '')
    # The file we pretend to compress
    ctx.create_dummy_out_file('Test.txt')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        patch_functions(m)
        pytest_wrapped_e = run_compress(ctx)
        pytest_wrapped_e2 = run_compress(ctx, test_import_fail=True)
    # Check we exited because rar isn't installed
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == WRONG_INSTALL
    assert "Failed to invoke rar command, error 10" in caplog.text
    # Not in the docker image ... pytest issue? (TODO)
    # assert "THE_ERROR" in caplog.text
    # Check we exited because the import failed
    assert pytest_wrapped_e2.type == SystemExit
    assert pytest_wrapped_e2.value.code == WRONG_INSTALL
    assert "Unable to import plug-ins:" in caplog.text


class NoGetTargets(BaseOutput):
    def __init__(self):
        self.options = True
        self.comment = 'Fake'
        self.name = 'dummy'
        self.type = 'none'
        self._sch_related = True


class DummyPre(BasePreFlight):
    def __init__(self):
        super().__init__('dummy', True)
        self._sch_related = True


def test_no_get_targets(caplog):
    test = NoGetTargets()
    test_pre = DummyPre()
    # Also check the dependencies fallback
    GS.sch = None
    GS.sch_file = 'fake'
    with context.cover_it(cov):
        test.get_targets('')
        files = test.get_dependencies()
        files_pre = test_pre.get_dependencies()
    assert "Output 'Fake' (dummy) [none] doesn't implement get_targets(), plese report it" in caplog.text
    assert files == [GS.sch_file]
    assert files_pre == [GS.sch_file]


def test_ibom_parse_fail(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    global mocked_check_output_retOK
    mocked_check_output_retOK = b'ERROR Parsing failed'
    # We will patch subprocess.check_output to make ibom fail
    with monkeypatch.context() as m:
        patch_functions(m)
        with context.cover_it(cov):
            detect_kicad()
            # Load the plug-ins
            load_actions()
            # Create an ibom object
            out = RegOutput.get_class_for('ibom')()
            out.set_tree({})
            out.config(None)
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                out.run('')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == BOM_ERROR
    # logging.debug(caplog.text)
    assert "Failed to create BoM" in caplog.text
    mocked_check_output_retOK = ''


def test_var_rename_no_variant():
    with context.cover_it(cov):
        # Load the plug-ins
        load_actions()
        # Create an ibom object
        filter = RegFilter.get_class_for('var_rename')()
        GS.variant = None
        # Should just return
        filter.filter(None)


def test_bom_no_sch():
    with context.cover_it(cov):
        # Load the plug-ins
        load_actions()
        # Create an ibom object
        GS.sch = None
        out = RegOutput.get_class_for('bom')()
        columns = out.options._get_columns()
        assert columns == ColumnList.COLUMNS_DEFAULT
        out = RegOutput.get_class_for('kibom')()
        options = out.options()
        columns = options.conf._get_columns()
        assert columns == ColumnList.COLUMNS_DEFAULT


def test_pre_xrc_fail(test_dir, caplog, monkeypatch):
    ctx = context.TestContext(test_dir, 'test_pre_xrc_fail', 'test_v5', 'empty_zip', '')
    global mocked_call_enabled
    mocked_call_enabled = True
    with monkeypatch.context() as m:
        patch_functions(m)
        with context.cover_it(cov):
            load_actions()
            GS.set_pcb(ctx.board_file)
            sch = ctx.board_file
            GS.set_sch(sch.replace('.kicad_pcb', '.sch'))
            GS.out_dir = test_dir
            pre_drc = BasePreFlight.get_class_for('run_drc')('run_drc', True)
            with pytest.raises(SystemExit) as e1:
                pre_drc.run()
            pre_erc = BasePreFlight.get_class_for('run_erc')('run_erc', True)
            with pytest.raises(SystemExit) as e2:
                pre_erc.run()
            out = RegOutput.get_class_for('pdf_pcb_print')()
            out.set_tree({'layers': 'all'})
            out.config(None)
            with pytest.raises(SystemExit) as e3:
                out.run('')
    assert e1.type == SystemExit
    assert e1.value.code == DRC_ERROR
    assert e2.type == SystemExit
    assert e2.value.code == ERC_ERROR
    assert e3.type == SystemExit
    assert e3.value.code == PDF_PCB_PRINT
    assert CMD_PCBNEW_PRINT_LAYERS+' returned 5' in caplog.text
    ctx.clean_up()
    mocked_call_enabled = False


def test_unimplemented_layer(caplog):
    with context.cover_it(cov):
        with pytest.raises(AssertionError) as e:
            Layer.solve(1)
    assert e.type == AssertionError
    assert e.value.args[0] == "Unimplemented layer type <class 'int'>"


def test_step_fail(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    # Create a silly context to get the output path
    ctx = context.TestContext(test_dir, 'test_step_fail', 'test_v5', 'empty_zip', '')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        patch_functions(m)
        with context.cover_it(cov):
            detect_kicad()
            load_actions()
            GS.set_pcb(ctx.board_file)
            GS.board = None
            KiConf.loaded = False
            load_board()
            # Create a compress object with the dummy file as source
            out = RegOutput.get_class_for('step')()
            out.set_tree({})
            out.config(None)
            with pytest.raises(SystemExit) as e:
                out.run('')
    # Check we exited because rar isn't installed
    assert e.type == SystemExit
    assert e.value.code == KICAD2STEP_ERR
    assert "Failed to create Step file, error 10" in caplog.text


def test_unknown_prefix(caplog):
    with context.cover_it(cov):
        get_prefix('y')
    assert 'Unknown prefix, please report' in caplog.text


def test_search_as_plugin_ok(test_dir, caplog):
    ctx = context.TestContext(test_dir, 'test_search_as_plugin_ok', 'test_v5', 'empty_zip', '')
    with context.cover_it(cov):
        detect_kicad()
        load_actions()
        dir_fake = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        GS.kicad_plugins_dirs.append(dir_fake)
        logging.debug('GS.kicad_plugins_dirs: '+str(GS.kicad_plugins_dirs))
        fname = search_as_plugin('fake', ['fake_plugin'])
        logging.debug('fname: '+fname)
        with open(ctx.get_out_path('error.txt'), 'wt') as f:
            f.write(caplog.text)
        # Fails to collect caplog on docker image (TODO)
        # This is a bizarre case, the test alone works, all tests in test_misc* together work.
        # But when running all the tests this one fails to get caplog.
        # The test_rar_fail has a similar problem.
        # assert re.search(r"Using `(.*)data/fake_plugin/fake` for `fake` \(fake_plugin\)", caplog.text) is not None
        assert re.search(r"(.*)data/fake_plugin/fake", fname) is not None
    ctx.clean_up()


def test_search_as_plugin_fail(test_dir, caplog):
    with context.cover_it(cov):
        detect_kicad()
        load_actions()
        dir_fake = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        GS.kicad_plugins_dirs.append(dir_fake)
        fname = search_as_plugin('fake', [''])
        assert fname == 'fake'


def test_layer_no_id():
    with context.cover_it(cov):
        la = Layer()
        la.layer = 'F.Cu'
        la.description = 'Top'
        la.suffix = 'F_Cu'
        assert str(la) == "F.Cu ('Top' F_Cu)"


def test_makefile_kibot_sys(test_dir):
    ctx = context.TestContext(test_dir, 'test_makefile_kibot_sys', 'test_v5', 'empty_zip', '')
    GS.sch_file = 'foo.sch'
    GS.pcb_file = 'bar.kicad_pcb'
    GS.out_dir = ctx.get_out_path('')
    with context.cover_it(cov):
        generate_makefile(ctx.get_out_path('Makefile'), 'pp', [], kibot_sys=True)
    ctx.search_in_file('Makefile', [r'KIBOT\?=kibot'])
    ctx.clean_up()
