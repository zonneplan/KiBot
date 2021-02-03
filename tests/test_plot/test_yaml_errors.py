"""
Tests various errors in the config file

- Wrong kibot
- No kibot.version
- Typo in kibot.version
- Wrong kibot.version
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
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
from kibot.misc import (EXIT_BAD_CONFIG, PLOT_ERROR, BOM_ERROR, WRONG_ARGUMENTS)


PRJ = 'fail-project'


def test_no_version(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorNoVersion', '3Rs', 'error_no_version', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs `kibot.version`.')
    ctx.clean_up()


def test_wrong_version(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongVersion', '3Rs', 'error_wrong_version', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Unknown KiBot config version: 20')
    ctx.clean_up()


def test_wrong_version_2(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongVersion2', '3Rs', 'error_wrong_version_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Incorrect .?kibot.? section')
    ctx.clean_up()


def test_wrong_version_3(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongVersion3', '3Rs', 'error_wrong_version_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs .?kibot.version.?')
    ctx.clean_up()


def test_drill_map_no_type_1(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillMapNoType1', '3Rs', 'error_drill_map_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?map.?")
    ctx.clean_up()


def test_drill_map_no_type_2(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillMapNoType2', '3Rs', 'error_drill_map_no_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?types.?")
    ctx.clean_up()


def test_drill_map_wrong_type_1(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillMapWrongType1', '3Rs', 'error_drill_map_wrong_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?type.? must be any of")
    ctx.clean_up()


def test_drill_map_wrong_type_2(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillMapWrongType2', '3Rs', 'error_drill_map_wrong_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?type.? must be a string")
    ctx.clean_up()


def test_drill_map_wrong_type_3(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillMapWrongType3', '3Rs', 'error_drill_map_wrong_type_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?map.? must be any of")
    ctx.clean_up()


def test_drill_report_no_type_1(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillReportNoType1', '3Rs', 'error_drill_report_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?report.?")
    ctx.clean_up()


def test_drill_report_no_type_2(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillReportNoType2', '3Rs', 'error_drill_report_no_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?filenames.?")
    ctx.clean_up()


def test_drill_report_wrong_type_2(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillReportWrongType2', '3Rs', 'error_drill_report_wrong_type_2', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?filename.? must be a string")
    ctx.clean_up()


def test_drill_report_wrong_type_3(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorDrillReportWrongType3', '3Rs', 'error_drill_report_wrong_type_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?report.? must be any of")
    ctx.clean_up()


def test_wrong_layer_1(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer1', '3Rs', 'error_wrong_layer_1', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer name: .?F.Bogus.?")
    ctx.clean_up()


def test_wrong_layer_2(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer2', '3Rs', 'error_wrong_layer_2', None)
    ctx.run(PLOT_ERROR)
    assert ctx.search_err("Inner layer (.*) is not valid for this board")
    ctx.clean_up()


def test_wrong_layer_3(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer3', '3Rs', 'error_wrong_layer_3', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Malformed inner layer name: .?Inner_1.?,")
    ctx.clean_up()


def test_wrong_layer_4(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer4', '3Rs', 'error_wrong_layer_4', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?layers.? must be any of")
    ctx.clean_up()


def test_wrong_layer_5(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer5', '3Rs', 'error_wrong_layer_5', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?bogus.?")
    ctx.clean_up()


def test_wrong_layer_6(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer6', '3Rs', 'error_wrong_layer_6', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty .?layer.? attribute")
    ctx.clean_up()


def test_wrong_layer_7(test_dir):
    """ List of numbers """
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer7', '3Rs', 'error_wrong_layer_7', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?layers.? must be any of")
    ctx.clean_up()


def test_wrong_layer_9(test_dir):
    """ A bogus string """
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer9', '3Rs', 'error_wrong_layer_9', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer spec: .?nada.?")
    ctx.clean_up()


def test_wrong_layer_8(test_dir):
    """ List of strings, but number in middle """
    ctx = context.TestContext(test_dir, 'ErrorWrongLayer8', '3Rs', 'error_wrong_layer_8', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?4.? must be any of")
    ctx.clean_up()


def test_no_name(test_dir):
    ctx = context.TestContext(test_dir, 'test_no_name', '3Rs', 'error_no_name', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output needs a name")
    ctx.clean_up()


def test_empty_name(test_dir):
    ctx = context.TestContext(test_dir, 'test_empty_name', '3Rs', 'error_empty_name', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output needs a name")
    ctx.clean_up()


def test_no_type(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorNoType', '3Rs', 'error_no_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output .PDF. needs a type")
    ctx.clean_up()


def test_out_unknown_attr(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorUnkOutAttr', '3Rs', 'error_unk_attr', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?directory.?")
    ctx.clean_up()


def test_out_needs_type(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorNeedsType', '3Rs', 'error_needs_type', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("needs a type")
    ctx.clean_up()


# Now is valid
# def test_no_options(test_dir):
#     ctx = context.TestContext(test_dir, 'ErrorNoOptions', '3Rs', 'error_no_options', None)
#     ctx.run(EXIT_BAD_CONFIG)
#     assert ctx.search_err("Output .PDF. needs options")
#     ctx.clean_up()


def test_no_layers(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorNoLayers', '3Rs', 'error_no_layers', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?layers.? list")
    ctx.clean_up()


def test_error_step_origin(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorStepOrigin', 'bom', 'error_step_origin', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Origin must be")
    ctx.clean_up()


def test_error_step_min_distance(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorStepMinDistance', 'bom', 'error_step_min_distance', None)
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?min_distance.? must be a number")
    ctx.clean_up()


def test_filter_not_list(test_dir):
    ctx = context.TestContext(test_dir, 'FilterNotList', PRJ, 'error_filter_not_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?filters.? must be any of")
    ctx.clean_up()


def test_filter_no_number(test_dir):
    ctx = context.TestContext(test_dir, 'FilterNoNumber', PRJ, 'error_filter_no_number', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?number.? must be a number")
    ctx.clean_up()


def test_filter_no_number_2(test_dir):
    ctx = context.TestContext(test_dir, 'FilterNoNumber2', PRJ, 'error_filter_no_number_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?error.?")
    ctx.clean_up()


def test_filter_no_regex(test_dir):
    ctx = context.TestContext(test_dir, 'FilterNoRegex', PRJ, 'error_filter_no_regex', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?regex.? must be a string")
    ctx.clean_up()


def test_filter_no_regex_2(test_dir):
    ctx = context.TestContext(test_dir, 'FilterNoRegex2', PRJ, 'error_filter_no_regex_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?regex.?")
    ctx.clean_up()


def test_filter_wrong_entry(test_dir):
    ctx = context.TestContext(test_dir, 'FilterWrongEntry', PRJ, 'error_filter_wrong_entry', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?numerito.?")
    ctx.clean_up()


def test_error_pre_list(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorPreList', PRJ, 'error_pre_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Incorrect .?preflight.? section")
    ctx.clean_up()


def test_error_pre_unk(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorPreUnk', PRJ, 'error_pre_unk', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown preflight: .?run_drcs.?")
    ctx.clean_up()


def test_error_wrong_type_1(test_dir):
    """ run_drc = number """
    ctx = context.TestContext(test_dir, 'ErrorWrongType1', PRJ, 'error_pre_wrong_type_1', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'run_drc': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_2(test_dir):
    """ ignore_unconnected = string """
    ctx = context.TestContext(test_dir, 'ErrorWrongType2', PRJ, 'error_pre_wrong_type_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'ignore_unconnected': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_3(test_dir):
    """ run_erc = number """
    ctx = context.TestContext(test_dir, 'ErrorWrongType3', PRJ, 'error_pre_wrong_type_3', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'run_erc': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_4(test_dir):
    """ update_xml = number """
    ctx = context.TestContext(test_dir, 'ErrorWrongType4', PRJ, 'error_pre_wrong_type_4', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'update_xml': must be boolean")
    ctx.clean_up()


def test_error_wrong_type_5(test_dir):
    """ check_zone_fills = number """
    ctx = context.TestContext(test_dir, 'ErrorWrongType5', PRJ, 'error_pre_wrong_type_5', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight 'check_zone_fills': must be boolean")
    ctx.clean_up()


def test_error_yaml(test_dir):
    ctx = context.TestContext(test_dir, 'ErrorYAML', PRJ, 'error_yaml', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Error loading YAML")
    ctx.clean_up()


def test_out_not_list(test_dir):
    ctx = context.TestContext(test_dir, 'OutNotList', PRJ, 'error_out_not_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?outputs.? must be a list")
    ctx.clean_up()


def test_unk_section(test_dir):
    ctx = context.TestContext(test_dir, 'UnkSection', PRJ, 'error_unk_section', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown section .?bogus.? in config")
    ctx.clean_up()


def test_error_hpgl_pen_num(test_dir):
    ctx = context.TestContext(test_dir, 'HPGLPenNum', PRJ, 'error_hpgl_pen_num', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?pen_number.? outside its range")
    ctx.clean_up()


def test_error_bom_wrong_format(test_dir):
    ctx = context.TestContext(test_dir, 'BoMWrongFormat', PRJ, 'error_bom_wrong_format', '')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom.sch')])
    assert ctx.search_err("Option .?format.? must be any of")
    ctx.clean_up()


def test_error_bom_column(test_dir):
    ctx = context.TestContext(test_dir, 'BoMColumn', PRJ, 'error_bom_column', '')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom.sch')])
    assert ctx.search_err("Invalid column name .?Impossible.?")
    ctx.clean_up()


def test_error_bom_no_columns(test_dir):
    ctx = context.TestContext(test_dir, 'BoMNoColumns', PRJ, 'error_bom_column', '')
    ctx.run(BOM_ERROR, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom_no_xml.sch')])
    assert ctx.search_err("Failed to get the column names")
    ctx.clean_up()


def test_error_bom_no_field(test_dir):
    ctx = context.TestContext(test_dir, 'BoMNoField', PRJ, 'error_bom_no_field', '')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'fail-erc.sch')])
    assert ctx.search_err("Missing or empty .?field.?")
    ctx.clean_up()


def test_error_wrong_boolean(test_dir):
    ctx = context.TestContext(test_dir, 'WrongBoolean', PRJ, 'error_wrong_boolean', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?exclude_edge_layer.? must be true/false")
    ctx.clean_up()


def test_error_gerber_precision(test_dir):
    ctx = context.TestContext(test_dir, 'GerberPrecisionError', PRJ, 'error_gerber_precision', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?gerber_precision.? must be 4.5 or 4.6")
    ctx.clean_up()


def test_error_wrong_drill_marks_1(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_wrong_drill_marks_1', PRJ, 'error_wrong_drill_marks', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown drill mark type: bogus")
    ctx.clean_up()


def test_error_wrong_drill_marks_2(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_wrong_drill_marks_2', PRJ, 'error_wrong_drill_marks_2', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown drill mark type: bogus")
    ctx.clean_up()


def test_error_print_pcb_no_layer(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'test_error_print_pcb_no_layer', prj, 'error_print_pcb_no_layer', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?layers.? list")
    ctx.clean_up()


def test_error_color(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_color', 'bom', 'error_color', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Invalid color for .?board.?")
    ctx.clean_up()


def test_wrong_global(test_dir):
    ctx = context.TestContext(test_dir, 'WrongGlobal', 'bom', 'error_wrong_global', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Incorrect .?global.? section")
    ctx.clean_up()


def test_goutput_not_string(test_dir):
    ctx = context.TestContext(test_dir, 'test_goutput_not_string', 'bom', 'error_goutput_not_string', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?output.? must be a string")
    ctx.clean_up()


def test_unk_global(test_dir):
    ctx = context.TestContext(test_dir, 'test_unk_global', 'bom', 'error_unk_global', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown global option")
    ctx.clean_up()


def test_error_int_bom_no_field(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_int_bom_no_field', 'links', 'error_int_bom_no_field', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty `field` in columns list")
    ctx.clean_up()


def test_error_int_bom_miss_logo(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_int_bom_miss_logo', 'links', 'error_int_bom_miss_logo', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing logo file")
    ctx.clean_up()


def test_error_int_bom_miss_style(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_int_bom_miss_style', 'links', 'error_int_bom_miss_style', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing style file")
    ctx.clean_up()


def test_error_int_bom_unknown_style(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_int_bom_unknown_style', 'links', 'error_int_bom_unknown_style', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown style .?bogus.?")
    ctx.clean_up()


def test_error_int_bom_invalid_col(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_int_bom_invalid_col', 'links', 'error_int_bom_invalid_col', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Invalid column name")
    ctx.clean_up()


def test_error_int_bom_logo_format(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_int_bom_logo_format', 'links', 'error_int_bom_logo_format', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Only PNG images are supported for the logo")
    ctx.clean_up()


def test_error_var_no_name(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_no_name', 'links', 'error_var_no_name', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant needs a name in:")
    ctx.clean_up()


def test_error_var_empty_name(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_empty_name', 'links', 'error_var_empty_name', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant needs a name in:")
    ctx.clean_up()


def test_error_var_wrong_type(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_wrong_type', 'links', 'error_var_wrong_type', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown variant type")
    ctx.clean_up()


def test_error_var_no_type(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_no_type', 'links', 'error_var_no_type', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant (.*) needs a type")
    ctx.clean_up()


def test_error_var_empty_type(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_empty_type', 'links', 'error_var_empty_type', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant (.*) needs a type")
    ctx.clean_up()


def test_error_var_no_list(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_no_list', 'links', 'error_var_no_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?variants.? must be a list")
    ctx.clean_up()


def test_error_fil_no_list(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_fil_no_list', 'links', 'error_fil_no_list', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?filters.? must be a list")
    ctx.clean_up()


def test_error_fil_unknown(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_fil_unknown', 'links', 'error_fil_unknown', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown filter (.*) used for ")
    ctx.clean_up()


def test_error_var_unknown(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_var_unknown', 'links', 'error_unk_variant', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown variant name")
    ctx.clean_up()


def test_error_wrong_fil_name(test_dir):
    ctx = context.TestContextSCH(test_dir, 'test_error_wrong_fil_name', 'links', 'error_wrong_fil_name', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Filter names starting with (.*) are reserved")
    ctx.clean_up()


def test_error_pcbdraw_comp_key(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_pcbdraw_comp_key', 'bom', 'error_pcbdraw_comp_key', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?show_components.? must be any of")
    ctx.clean_up()


def test_error_rot_not_two(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_rot_not_two', 'bom', 'error_rot_not_two', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Each regex/angle pair must contain exactly two values")
    ctx.clean_up()


def test_error_rot_not_number(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_rot_not_number', 'bom', 'error_rot_not_number', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("The second value in the regex/angle pairs must be a number")
    ctx.clean_up()


def test_error_rot_no_rotations(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_rot_no_rotations', 'bom', 'error_rot_no_rotations', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("No rotations provided")
    ctx.clean_up()


def test_error_makefile_wrong_out(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_makefile_wrong_out', 'bom', 'error_makefile_wrong_out', '')
    ctx.run(WRONG_ARGUMENTS)
    assert ctx.search_err("Unknown output `position` selected in")
    ctx.clean_up()


def test_error_no_column_id(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_no_column_id', 'bom', 'error_no_column_id', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty `id` in columns list")
    ctx.clean_up()


def test_error_aggregate_no_file(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_aggregate_no_file', 'bom', 'error_aggregate_no_file', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty `file` in aggregate list")
    ctx.clean_up()


def test_error_aggregate_miss_file(test_dir):
    ctx = context.TestContext(test_dir, 'test_error_aggregate_miss_file', 'bom', 'error_aggregate_miss_file', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing `dummy`")
    ctx.clean_up()
