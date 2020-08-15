"""
Tests for KiCad configuration load


For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
import pytest
import coverage
import logging
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
from kiplot.misc import EXIT_BAD_CONFIG
from kiplot.kicad.config import KiConf, KiConfError
from kiplot.gs import GS


cov = coverage.Coverage()


def test_kicad_conf_bad_sym_lib_table():
    """ Check various problems in the sym-lib-table file """
    sch = 'sym-lib-table_errors/kibom-test'
    test = 'test_kicad_conf_bad_sym_lib_table'
    ctx = context.TestContextSCH(test, sch, 'int_bom_simple_csv', None)
    ctx.run(EXIT_BAD_CONFIG, extra_debug=True)
    ctx.search_err('Malformed lib entry')
    ctx.search_err(r'Unable to expand .?BOGUS.? in')
    ctx.search_err(r'unnamed LibAlias')
    ctx.clean_up()


def test_kicad_conf_no_instance():
    """ Check we can't create a KiConf instance """
    cov.load()
    cov.start()
    with pytest.raises(AssertionError) as pytest_wrapped_e:
        o = KiConf()  # noqa: F841
    cov.stop()
    cov.save()
    assert pytest_wrapped_e.type == AssertionError
    assert str(pytest_wrapped_e.value) == 'KiConf is fully static, no instances allowed'


def kiconf_de_init():
    KiConf.loaded = False
    KiConf.config_dir = None
    KiConf.dirname = None
    KiConf.sym_lib_dir = None
    KiConf.kicad_env = {}
    KiConf.lib_aliases = {}


def check_load_conf(caplog, dir='kicad', fail=False):
    caplog.set_level(logging.DEBUG)
    kiconf_de_init()
    cov.load()
    cov.start()
    with pytest.raises(KiConfError) as pytest_wrapped_e:
        KiConf.init(os.path.join(context.BOARDS_DIR, 'v5_errors/kibom-test.sch'))
    cov.stop()
    cov.save()
    ref = 'Reading KiCad config from `tests/data/'+dir+'/kicad_common`'
    if fail:
        ref = 'Unable to find KiCad configuration file'
    assert ref in caplog.text, caplog.text
    return pytest_wrapped_e


def test_kicad_conf_user(caplog):
    """ Check we can load the KiCad configuration from $KICAD_CONFIG_HOME """
    old = os.environ.get('KICAD_CONFIG_HOME')
    os.environ['KICAD_CONFIG_HOME'] = 'tests/data/kicad_ok'
    GS.debug_level = 2
    check_load_conf(caplog, dir='kicad_ok')
    assert 'KICAD_TEMPLATE_DIR="/usr/share/kicad/template"' in caplog.text, caplog.text
    if old:
        os.environ['KICAD_CONFIG_HOME'] = old
    else:
        del os.environ['KICAD_CONFIG_HOME']


def test_kicad_conf_xdg(caplog):
    """ Check we can load the KiCad configuration from $XDG_CONFIG_HOME/kicad """
    old = os.environ.get('XDG_CONFIG_HOME')
    os.environ['XDG_CONFIG_HOME'] = 'tests/data'
    check_load_conf(caplog)
    assert 'KiCad config without EnvironmentVariables section' in caplog.text, caplog.text
    if old:
        os.environ['XDG_CONFIG_HOME'] = old
    else:
        del os.environ['XDG_CONFIG_HOME']


def test_kicad_conf_miss_home(caplog):
    """ Check no HOME and fail to load kicad_common.
        Also check we correctly guess the libs dir. """
    old = os.environ['HOME']
    del os.environ['HOME']
    check_load_conf(caplog, fail=True)
    os.environ['HOME'] = old
    assert '`HOME` not defined' in caplog.text, caplog.text
    assert 'Detected KICAD_SYMBOL_DIR="/usr/share/kicad/library"' in caplog.text, caplog.text


def test_kicad_conf_lib_env(caplog):
    """ Check we can use KICAD_SYMBOL_DIR as fallback """
    old = os.environ['HOME']
    del os.environ['HOME']
    os.environ['KICAD_SYMBOL_DIR'] = 'tests'
    check_load_conf(caplog, fail=True)
    os.environ['HOME'] = old
    del os.environ['KICAD_SYMBOL_DIR']
    assert '`HOME` not defined' in caplog.text, caplog.text
    assert 'Detected KICAD_SYMBOL_DIR="tests"' in caplog.text, caplog.text


def test_kicad_conf_sym_err_1(caplog):
    """ Test broken sym-lib-table, no signature """
    old = os.environ.get('KICAD_CONFIG_HOME')
    os.environ['KICAD_CONFIG_HOME'] = 'tests/data/kicad_err_1'
    GS.debug_level = 2
    err = check_load_conf(caplog, dir='kicad_err_1')
    assert err.type == KiConfError
    assert err.value.msg == 'Symbol libs table missing signature'
    assert err.value.line == 1
    if old:
        os.environ['KICAD_CONFIG_HOME'] = old
    else:
        del os.environ['KICAD_CONFIG_HOME']


def test_kicad_conf_sym_err_2(caplog):
    """ Test broken sym-lib-table, wrong entry """
    old = os.environ.get('KICAD_CONFIG_HOME')
    os.environ['KICAD_CONFIG_HOME'] = 'tests/data/kicad_err_2'
    GS.debug_level = 2
    err = check_load_conf(caplog, dir='kicad_err_2')
    assert err.type == KiConfError
    assert err.value.msg == 'Unknown symbol table entry'
    assert err.value.line == 2
    if old:
        os.environ['KICAD_CONFIG_HOME'] = old
    else:
        del os.environ['KICAD_CONFIG_HOME']
