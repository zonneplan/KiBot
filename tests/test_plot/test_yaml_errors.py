"""
Tests various errors in the config file

- No kiplot.version
- Wrong kiplot.version

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(prev_dir))
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiplot.misc import (EXIT_BAD_CONFIG)


def test_no_version():
    ctx = context.TestContext('ErrorNoVersion', '3Rs', 'error_no_version', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs kiplot.version')
    ctx.clean_up()


def test_wrong_version():
    ctx = context.TestContext('ErrorWrongVersion', '3Rs', 'error_wrong_version', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Unknown KiPlot config version: 20')
    ctx.clean_up()
