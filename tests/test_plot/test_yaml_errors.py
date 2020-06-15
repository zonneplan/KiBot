"""
Tests various errors in the config file

- No kiplot.version
- Wrong kiplot.version
- Missing drill map type
- Wrong drill map type
- Wrong step origin
- Wrong step min_distance
- Wrong layer:
  - Incorrect name
  - Inner.1, but no inner layers
  - Inner_1 (malformed)
- No output:
  - name
  - type
  - options
  - layers

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
from kiplot.misc import (EXIT_BAD_CONFIG, PLOT_ERROR)


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


def test_drill_map_no_type():
    ctx = context.TestContext('ErrorDrillMapNoType', '3Rs', 'error_drill_map_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing `type' in drill map section")
    ctx.clean_up()


def test_drill_map_wrong_type():
    ctx = context.TestContext('ErrorDrillMapWrongType', '3Rs', 'error_drill_map_wrong_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown drill map type: bogus")
    ctx.clean_up()


def test_wrong_layer_1():
    ctx = context.TestContext('ErrorWrongLayer1', '3Rs', 'error_wrong_layer_1', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer name: F.Bogus")
    ctx.clean_up()


def test_wrong_layer_2():
    ctx = context.TestContext('ErrorWrongLayer2', '3Rs', 'error_wrong_layer_2', None)
    ctx.run(PLOT_ERROR)
    assert ctx.search_err("Inner layer 1 is not valid for this board")
    ctx.clean_up()


def test_wrong_layer_3():
    ctx = context.TestContext('ErrorWrongLayer3', '3Rs', 'error_wrong_layer_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Malformed inner layer name: Inner_1,")
    ctx.clean_up()


def test_no_name():
    ctx = context.TestContext('ErrorNoName', '3Rs', 'error_no_name', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output needs a name")
    ctx.clean_up()


def test_no_type():
    ctx = context.TestContext('ErrorNoType', '3Rs', 'error_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output 'PDF' needs a type")
    ctx.clean_up()


def test_no_options():
    ctx = context.TestContext('ErrorNoOptions', '3Rs', 'error_no_options', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output 'PDF' needs options")
    ctx.clean_up()


def test_no_layers():
    ctx = context.TestContext('ErrorNoLayers', '3Rs', 'error_no_layers', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("You must specify the layers for `PDF`")
    ctx.clean_up()


def test_error_step_origin():
    ctx = context.TestContext('ErrorStepOrigin', 'bom', 'error_step_origin', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Origin must be")
    ctx.clean_up()


def test_error_step_min_distance():
    ctx = context.TestContext('ErrorStepMinDistance', 'bom', 'error_step_min_distance', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("min_distance must be a number")
    ctx.clean_up()
