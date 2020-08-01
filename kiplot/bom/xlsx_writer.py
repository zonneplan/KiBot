# -*- coding: utf-8 -*-
"""
XLSX Writer:
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

Generates an XLSX file.
"""
# TODO: alternate colors, set row height, put logo, move data to beginning
from .columnlist import ColumnList
from .. import log
try:
    from xlsxwriter import Workbook
    XLSX_SUPPORT = True
except ModuleNotFoundError:
    XLSX_SUPPORT = False

    class Workbook():
        pass

logger = log.get_logger(__name__)
MAX_WIDTH = 60
BG_GEN = "#E6FFEE"
BG_KICAD = "#FFE6B3"
BG_USER = "#E6F9FF"
BG_EMPTY = "#FF8080"
DEFAULT_FMT = {'text_wrap': True, 'align': 'center_across', 'valign': 'vjustify'}


def bg_color(col):
    """ Return a background color for a given column title """
    col = col.lower()
    # Auto-generated columns
    if col in ColumnList.COLUMNS_GEN_L:
        return BG_GEN
    # KiCad protected columns
    elif col in ColumnList.COLUMNS_PROTECTED_L:
        return BG_KICAD
    # Additional user columns
    return BG_USER


def add_info(worksheet, column_widths, row, formats, text, value):
    worksheet.write_string(row, 0, text, formats[0])
    if isinstance(value, (int, float)):
        worksheet.write_number(row, 1, value, formats[1])
        value = str(value)
    else:
        worksheet.write_string(row, 1, value, formats[1])
    value_l = len(value)
    if value_l > column_widths[1]:
        column_widths[1] = value_l
    return row + 1


def write_xlsx(filename, groups, col_fields, head_names, cfg):
    """
    Write BoM out to a XLSX file
    filename = path to output file (must be a .xlsx file)
    groups = [list of ComponentGroup groups]
    col_fields = [list of col_fields to search for data in the BoM file]
    head_names = [list of col_fields to display in the BoM file]
    prefs = BomPref object
    """
    if not XLSX_SUPPORT:
        logger.error('Python xlsxwriter module not installed (Debian: python3-xlsxwriter)')
        return False

    workbook = Workbook(filename)
    worksheet = workbook.add_worksheet()

    if cfg.number_rows:
        comp = "Component"
        if comp.lower() in cfg.column_rename:
            comp = cfg.column_rename[comp.lower()]
        row_headings = [comp] + head_names
    else:
        row_headings = head_names

    # Headings
    cellformats = {}
    column_widths = {}
    for i in range(len(row_headings)):
        cellformats[i] = workbook.add_format(DEFAULT_FMT)
        bg = None
        if cfg.number_rows:
            if i > 0:
                bg = bg_color(col_fields[i-1])
        else:
            bg = bg_color(col_fields[i])
        if bg:
            cellformats[i].set_bg_color(bg)
        column_widths[i] = len(row_headings[i]) + 10
        if not cfg.hide_headers:
            fmt = workbook.add_format(DEFAULT_FMT)
            fmt.set_bold()
            if bg:
                fmt.set_bg_color(bg)
            worksheet.write_string(0, i, row_headings[i], fmt)
    empty_fmt = workbook.add_format(DEFAULT_FMT)
    empty_fmt.set_bg_color(BG_EMPTY)

    # Body
    row_count = 1
    for i, group in enumerate(groups):
        if cfg.ignore_dnf and not group.is_fitted():
            continue
        # Get the data row
        row = group.get_row(col_fields)
        # Add row number
        if cfg.number_rows:
            row = [str(row_count)] + row
        # Fill the row
        for i in range(len(row)):
            cell = row[i]
            fmt = cellformats[i]
            if len(cell) == 0 or cell.strip() == "~":
                fmt = empty_fmt
            worksheet.write_string(row_count, i, cell, fmt)
            if len(cell) > column_widths[i] - 5:
                column_widths[i] = len(cell) + 5
        row_count += 1

    # PCB Info
    if not cfg.hide_pcb_info:
        # Add a few blank rows
        for i in range(5):
            row_count += 1
        # Data left justified
        cellformat_left = workbook.add_format({'align': 'left'})
        title_fmt = workbook.add_format(DEFAULT_FMT)
        title_fmt.set_bold()

        formats = [title_fmt, cellformat_left]
        row_count = add_info(worksheet, column_widths, row_count, formats, "Component Groups:", cfg.n_groups)
        row_count = add_info(worksheet, column_widths, row_count, formats, "Component Count:", cfg.n_total)
        row_count = add_info(worksheet, column_widths, row_count, formats, "Fitted Components:", cfg.n_fitted)
        row_count = add_info(worksheet, column_widths, row_count, formats, "Number of PCBs:", cfg.number)
        row_count = add_info(worksheet, column_widths, row_count, formats, "Total components:", cfg.n_build)
        row_count = add_info(worksheet, column_widths, row_count, formats, "Schematic Revision:", cfg.revision)
        row_count = add_info(worksheet, column_widths, row_count, formats, "Schematic Date:", cfg.date)
        # row_count = add_info(worksheet, column_widths, row_count, formats, "BoM Date:", cfg.date) Same as sch
        row_count = add_info(worksheet, column_widths, row_count, formats, "Schematic Date:", cfg.source)
        # row_count = add_info(worksheet, column_widths, row_count, formats, "KiCad Version:", ) TODO?

    # Adjust the widths
    for i in range(len(column_widths)):
        width = column_widths[i]
        if width > MAX_WIDTH:
            width = MAX_WIDTH
        worksheet.set_column(i, i, width)

    workbook.close()

    return True
