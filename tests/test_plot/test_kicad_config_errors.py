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
from kiplot.kicad.config import KiConf


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


def check_load_conf(caplog):
    caplog.set_level(logging.DEBUG)
    cov.load()
    cov.start()
    KiConf.init(os.path.join(context.BOARDS_DIR, 'v5_errors/kibom-test.sch'))
    cov.stop()
    cov.save()
    assert len(caplog.text)
    assert 'Reading KiCad config from `tests/data/kicad/kicad_common`' in caplog.text


def test_kicad_conf_user(caplog):
    """ Check we can load the KiCad configuration from $KICAD_CONFIG_HOME """
    os.environ['KICAD_CONFIG_HOME'] = 'tests/data/kicad'
    check_load_conf(caplog)
    del os.environ['KICAD_CONFIG_HOME']


def test_kicad_conf_xdg(caplog):
    """ Check we can load the KiCad configuration from $KICAD_CONFIG_HOME """
    os.environ['XDG_CONFIG_HOME'] = 'tests/data'
    check_load_conf(caplog)
    del os.environ['XDG_CONFIG_HOME']
