"""
Tests various errors in the config file

- Wrong kiplot
- No kiplot.version
- Typo in kiplot.version
- Wrong kiplot.version
- Missing drill map type
- Wrong drill map type
- Wrong step origin
- Wrong step min_distance
- Wrong layer:
  - Incorrect name
  - Inner.1, but no inner layers
  - Inner_1 (malformed)
  - Not a list
  - Unknown attribute
  - No layer attribute
- No output:
  - name
  - type
  - layers
- Output:
  - with unknown attribute
  - Not a list
- Filters:
  - Not a list
  - Empty number
  - No number
  - Empty regex
  - No regex
  - No filter
- Pre-flight:
  - Not a list
  - Unknown entry
  - Wrong type for entry (run_drc)
- YAML syntax
- Unknown section
- HPGL wrong pen_number
- KiBoM wrong format
  - Invalid column name
  - Failed to get columns
  - Column without field
- PcbDraw
  - Wrong color

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
from kiplot.misc import (EXIT_BAD_CONFIG, PLOT_ERROR, BOM_ERROR)


PRJ = 'fail-project'


def test_no_version():
    ctx = context.TestContext('ErrorNoVersion', '3Rs', 'error_no_version', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs `kiplot.version`.')
    ctx.clean_up()


def test_wrong_version():
    ctx = context.TestContext('ErrorWrongVersion', '3Rs', 'error_wrong_version', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Unknown KiPlot config version: 20')
    ctx.clean_up()


def test_wrong_version_2():
    ctx = context.TestContext('ErrorWrongVersion2', '3Rs', 'error_wrong_version_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Incorrect .?kiplot.? section')
    ctx.clean_up()


def test_wrong_version_3():
    ctx = context.TestContext('ErrorWrongVersion3', '3Rs', 'error_wrong_version_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs .?kiplot.version.?')
    ctx.clean_up()


def test_drill_map_no_type_1():
    ctx = context.TestContext('ErrorDrillMapNoType1', '3Rs', 'error_drill_map_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?map.?")
    ctx.clean_up()


def test_drill_map_no_type_2():
    ctx = context.TestContext('ErrorDrillMapNoType2', '3Rs', 'error_drill_map_no_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?types.?")
    ctx.clean_up()


def test_drill_map_wrong_type_1():
    ctx = context.TestContext('ErrorDrillMapWrongType1', '3Rs', 'error_drill_map_wrong_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?type.? must be any of")
    ctx.clean_up()


def test_drill_map_wrong_type_2():
    ctx = context.TestContext('ErrorDrillMapWrongType2', '3Rs', 'error_drill_map_wrong_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?type.? must be a string")
    ctx.clean_up()


def test_drill_map_wrong_type_3():
    ctx = context.TestContext('ErrorDrillMapWrongType3', '3Rs', 'error_drill_map_wrong_type_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?map.? must be any of")
    ctx.clean_up()


def test_drill_report_no_type_1():
    ctx = context.TestContext('ErrorDrillReportNoType1', '3Rs', 'error_drill_report_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?report.?")
    ctx.clean_up()


def test_drill_report_no_type_2():
    ctx = context.TestContext('ErrorDrillReportNoType2', '3Rs', 'error_drill_report_no_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?filenames.?")
    ctx.clean_up()


def test_drill_report_wrong_type_2():
    ctx = context.TestContext('ErrorDrillReportWrongType2', '3Rs', 'error_drill_report_wrong_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?filename.? must be a string")
    ctx.clean_up()


def test_drill_report_wrong_type_3():
    ctx = context.TestContext('ErrorDrillReportWrongType3', '3Rs', 'error_drill_report_wrong_type_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?report.? must be any of")
    ctx.clean_up()


def test_wrong_layer_1():
    ctx = context.TestContext('ErrorWrongLayer1', '3Rs', 'error_wrong_layer_1', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer name: .?F.Bogus.?")
    ctx.clean_up()


def test_wrong_layer_2():
    ctx = context.TestContext('ErrorWrongLayer2', '3Rs', 'error_wrong_layer_2', None)
    ctx.run(PLOT_ERROR)
    assert ctx.search_err("Inner layer (.*) is not valid for this board")
    ctx.clean_up()


def test_wrong_layer_3():
    ctx = context.TestContext('ErrorWrongLayer3', '3Rs', 'error_wrong_layer_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Malformed inner layer name: .?Inner_1.?,")
    ctx.clean_up()


def test_wrong_layer_4():
    ctx = context.TestContext('ErrorWrongLayer4', '3Rs', 'error_wrong_layer_4', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?layers.? must be any of")
    ctx.clean_up()


def test_wrong_layer_5():
    ctx = context.TestContext('ErrorWrongLayer5', '3Rs', 'error_wrong_layer_5', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?bogus.?")
    ctx.clean_up()


def test_wrong_layer_6():
    ctx = context.TestContext('ErrorWrongLayer6', '3Rs', 'error_wrong_layer_6', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty .?layer.? attribute")
    ctx.clean_up()


def test_wrong_layer_7():
    """ List of numbers """
    ctx = context.TestContext('ErrorWrongLayer7', '3Rs', 'error_wrong_layer_7', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?layers.? must be any of")
    ctx.clean_up()


def test_wrong_layer_9():
    """ A bogus string """
    ctx = context.TestContext('ErrorWrongLayer9', '3Rs', 'error_wrong_layer_9', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer spec: .?nada.?")
    ctx.clean_up()


def test_wrong_layer_8():
    """ List of strings, but number in middle """
    ctx = context.TestContext('ErrorWrongLayer8', '3Rs', 'error_wrong_layer_8', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?4.? must be any of")
    ctx.clean_up()


def test_no_name():
    ctx = context.TestContext('ErrorNoName', '3Rs', 'error_no_name', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output needs a name")
    ctx.clean_up()


def test_no_type():
    ctx = context.TestContext('ErrorNoType', '3Rs', 'error_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output .PDF. needs a type")
    ctx.clean_up()


def test_out_unknown_attr():
    ctx = context.TestContext('ErrorUnkOutAttr', '3Rs', 'error_unk_attr', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?directory.?")
    ctx.clean_up()


def test_out_needs_type():
    ctx = context.TestContext('ErrorNeedsType', '3Rs', 'error_needs_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("needs a type")
    ctx.clean_up()


# Now is valid
# def test_no_options():
#     ctx = context.TestContext('ErrorNoOptions', '3Rs', 'error_no_options', None)
#     ctx.run(EXIT_BAD_CONFIG)
#     assert ctx.search_err("Output .PDF. needs options")
#     ctx.clean_up()


def test_no_layers():
    ctx = context.TestContext('ErrorNoLayers', '3Rs', 'error_no_layers', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?layers.? list")
    ctx.clean_up()


def test_error_step_origin():
    ctx = context.TestContext('ErrorStepOrigin', 'bom', 'error_step_origin', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Origin must be")
    ctx.clean_up()


def test_error_step_min_distance():
    ctx = context.TestContext('ErrorStepMinDistance', 'bom', 'error_step_min_distance', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?min_distance.? must be a number")
    ctx.clean_up()


def test_filter_not_list():
    ctx = context.TestContext('FilterNotList', PRJ, 'error_filter_not_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?filters.? must be any of")
    ctx.clean_up()


def test_filter_no_number():
    ctx = context.TestContext('FilterNoNumber', PRJ, 'error_filter_no_number', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?number.? must be a number")
    ctx.clean_up()


def test_filter_no_number_2():
    ctx = context.TestContext('FilterNoNumber2', PRJ, 'error_filter_no_number_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?number.?")
    ctx.clean_up()


def test_filter_no_regex():
    ctx = context.TestContext('FilterNoRegex', PRJ, 'error_filter_no_regex', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?regex.? must be a string")
    ctx.clean_up()


def test_filter_no_regex_2():
    ctx = context.TestContext('FilterNoRegex2', PRJ, 'error_filter_no_regex_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?regex.?")
    ctx.clean_up()


def test_filter_wrong_entry():
    ctx = context.TestContext('FilterWrongEntry', PRJ, 'error_filter_wrong_entry', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?numerito.?")
    ctx.clean_up()


def test_error_pre_list():
    ctx = context.TestContext('ErrorPreList', PRJ, 'error_pre_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Incorrect .?preflight.? section")
    ctx.clean_up()


def test_error_pre_unk():
    ctx = context.TestContext('ErrorPreUnk', PRJ, 'error_pre_unk', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown preflight: .?run_drcs.?")
    ctx.clean_up()


def test_error_wrong_type_1():
    """ run_drc = number """
    ctx = context.TestContext('ErrorWrongType1', PRJ, 'error_pre_wrong_type_1', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'run_drc': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_2():
    """ ignore_unconnected = string """
    ctx = context.TestContext('ErrorWrongType2', PRJ, 'error_pre_wrong_type_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'ignore_unconnected': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_3():
    """ run_erc = number """
    ctx = context.TestContext('ErrorWrongType3', PRJ, 'error_pre_wrong_type_3', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'run_erc': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_4():
    """ update_xml = number """
    ctx = context.TestContext('ErrorWrongType4', PRJ, 'error_pre_wrong_type_4', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'update_xml': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_5():
    """ check_zone_fills = number """
    ctx = context.TestContext('ErrorWrongType5', PRJ, 'error_pre_wrong_type_5', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'check_zone_fills': must be boolean")
    ctx.clean_up()


def test_error_yaml():
    ctx = context.TestContext('ErrorYAML', PRJ, 'error_yaml', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Error loading YAML")
    ctx.clean_up()


def test_out_not_list():
    ctx = context.TestContext('OutNotList', PRJ, 'error_out_not_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?outputs.? must be a list")
    ctx.clean_up()


def test_unk_section():
    ctx = context.TestContext('UnkSection', PRJ, 'error_unk_section', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown section .?bogus.? in config")
    ctx.clean_up()


def test_error_hpgl_pen_num():
    ctx = context.TestContext('HPGLPenNum', PRJ, 'error_hpgl_pen_num', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?pen_number.? outside its range")
    ctx.clean_up()


def test_error_bom_wrong_format():
    ctx = context.TestContext('BoMWrongFormat', PRJ, 'error_bom_wrong_format', '')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom.sch')])
    assert ctx.search_err("Option .?format.? must be any of")
    ctx.clean_up()


def test_error_bom_column():
    ctx = context.TestContext('BoMColumn', PRJ, 'error_bom_column', '')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom.sch')])
    assert ctx.search_err("Invalid column name .?Impossible.?")
    ctx.clean_up()


def test_error_bom_no_columns():
    ctx = context.TestContext('BoMNoColumns', PRJ, 'error_bom_column', '')
    ctx.run(BOM_ERROR, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom_no_xml.sch')])
    assert ctx.search_err("Failed to get the column names")
    ctx.clean_up()


def test_error_bom_no_field():
    ctx = context.TestContext('BoMNoField', PRJ, 'error_bom_no_field', '')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'fail-erc.sch')])
    assert ctx.search_err("Missing or empty .?field.?")
    ctx.clean_up()


def test_error_wrong_boolean():
    ctx = context.TestContext('WrongBoolean', PRJ, 'error_wrong_boolean', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?exclude_edge_layer.? must be true/false")
    ctx.clean_up()


def test_error_gerber_precision():
    ctx = context.TestContext('GerberPrecisionError', PRJ, 'error_gerber_precision', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?gerber_precision.? must be 4.5 or 4.6")
    ctx.clean_up()


def test_error_wrong_drill_marks():
    ctx = context.TestContext('WrongDrillMarks', PRJ, 'error_wrong_drill_marks', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown drill mark type: bogus")
    ctx.clean_up()


def test_error_print_pcb_no_layer():
    prj = 'bom'
    ctx = context.TestContext('PrPCB', prj, 'error_print_pcb_no_layer', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?layers.? list")
    ctx.clean_up()


def test_error_color():
    ctx = context.TestContext('PrPCB', 'bom', 'error_color', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Invalid color for .?board.?")
    ctx.clean_up()
