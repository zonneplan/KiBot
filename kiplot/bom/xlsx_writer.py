# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
"""
XLSX Writer: Generates an XLSX BoM file.
"""
import io
from textwrap import wrap
from base64 import b64decode
from .columnlist import ColumnList
from .kibot_logo import KIBOT_LOGO
from .. import log
try:
    from xlsxwriter import Workbook
    XLSX_SUPPORT = True
except ModuleNotFoundError:
    XLSX_SUPPORT = False

    class Workbook():
        pass

logger = log.get_logger(__name__)
BG_GEN = "#E6FFEE"
BG_KICAD = "#FFE6B3"
BG_USER = "#E6F9FF"
BG_EMPTY = "#FF8080"
BG_GEN_L = "#F0FFF4"
BG_KICAD_L = "#FFF0BD"
BG_USER_L = "#F0FFFF"
BG_EMPTY_L = "#FF8A8A"
BG_COLORS = [[BG_GEN, BG_GEN_L], [BG_KICAD, BG_KICAD_L], [BG_USER, BG_USER_L], [BG_EMPTY, BG_EMPTY_L]]
GREY = "#dddddd"
GREY_L = "#f3f3f3"
HEAD_COLOR_R = "#982020"
HEAD_COLOR_G = "#009879"
HEAD_COLOR_B = "#0e4e8e"
DEFAULT_FMT = {'text_wrap': True, 'align': 'center_across', 'valign': 'vjustify'}


def bg_color(col):
    """ Return a background color for a given column title """
    col = col.lower()
    # Auto-generated columns
    if col in ColumnList.COLUMNS_GEN_L:
        return 0
    # KiCad protected columns
    elif col in ColumnList.COLUMNS_PROTECTED_L:
        return 1
    # Additional user columns
    return 2


def add_info(worksheet, column_widths, row, col_offset, formats, text, value):
    worksheet.write_string(row, col_offset, text, formats[0])
    if isinstance(value, (int, float)):
        worksheet.write_number(row, col_offset+1, value, formats[1])
        value = str(value)
    else:
        worksheet.write_string(row, col_offset+1, value, formats[1])
    column_widths[col_offset] = max(len(text)+1, column_widths[col_offset])
    column_widths[col_offset+1] = max(len(value), column_widths[col_offset+1])
    return row + 1


def compute_head_size(cfg):
    head_size = 7
    if cfg.xlsx.logo is None:
        if not cfg.xlsx.title:
            head_size -= 1
        if cfg.xlsx.hide_pcb_info and cfg.xlsx.hide_stats_info:
            head_size -= 5
        if head_size == 1:
            head_size = 0
    return head_size


def create_fmt_head(workbook, style_name):
    fmt_head = workbook.add_format(DEFAULT_FMT)
    fmt_head.set_bold()
    if style_name.startswith('modern-'):
        if style_name.endswith('green'):
            head_color = HEAD_COLOR_G
        elif style_name.endswith('blue'):
            head_color = HEAD_COLOR_B
        else:
            head_color = HEAD_COLOR_R
        fmt_head.set_bg_color(head_color)
        fmt_head.set_font_color("#ffffff")
    return fmt_head


def get_logo_data(logo):
    if logo is not None:
        if logo:
            with open(logo, 'rb') as f:
                image_data = f.read()
        else:
            image_data = b64decode(KIBOT_LOGO)
    else:
        image_data = None
    return image_data


def create_fmt_title(workbook, title):
    if not title:
        return None
    fmt_title = workbook.add_format(DEFAULT_FMT)
    fmt_title.set_font_size(24)
    fmt_title.set_bold()
    fmt_title.set_font_name('Arial')
    fmt_title.set_align('left')
    return fmt_title


def create_fmt_cols(workbook, col_colors):
    """ Create the possible column formats """
    fmt_cols = []
    if col_colors:
        for c in BG_COLORS:
            fmts = [None, None]
            fmts[0] = workbook.add_format(DEFAULT_FMT)
            fmts[1] = workbook.add_format(DEFAULT_FMT)
            fmts[0].set_bg_color(c[0])
            fmts[1].set_bg_color(c[1])
            fmt_cols.append(fmts)
    else:
        fmts = [None, None]
        fmts[0] = workbook.add_format(DEFAULT_FMT)
        fmts[1] = workbook.add_format(DEFAULT_FMT)
        fmts[0].set_bg_color(GREY)
        fmts[1].set_bg_color(GREY_L)
        fmt_cols.append(fmts)
    return fmt_cols


def create_col_fmt(col_fields, col_colors, fmt_cols):
    """ Assign a color to each column """
    col_fmt = []
    if col_colors:
        for c in col_fields:
            col_fmt.append(fmt_cols[bg_color(c)])
    else:
        for c in col_fields:
            col_fmt.append(fmt_cols[0])
    # Empty color
    col_fmt.append(fmt_cols[-1])
    return col_fmt


def create_fmt_info(workbook, cfg):
    """ Formats for the PCB and stats info """
    if cfg.xlsx.hide_pcb_info and cfg.xlsx.hide_stats_info:
        return None
    # Data left justified
    fmt_data = workbook.add_format({'align': 'left'})
    fmt_name = workbook.add_format(DEFAULT_FMT)
    fmt_name.set_bold()
    fmt_name.set_align('left')
    return [fmt_name, fmt_data]


def insert_logo(worksheet, image_data):
    """ Inserts the logo, returns how many columns we used """
    if image_data:
        # Note: OpenOffice doesn't support using images in the header for XLSXs
        # worksheet.set_header('&L&[Picture]', {'image_left': 'logo.png', 'image_data_left': image_data})
        worksheet.insert_image('A1', 'logo.png', {'image_data': io.BytesIO(image_data), 'x_scale': 2, 'y_scale': 2})
        return 2
    return 0


def create_color_ref(workbook, col_colors, hl_empty, fmt_cols):
    if col_colors:
        worksheet = workbook.add_worksheet('Colors')
        worksheet.write_string(0, 0, 'KiCad Fields (default)', fmt_cols[0][0])
        worksheet.write_string(1, 0, 'Generated Fields', fmt_cols[1][0])
        worksheet.write_string(2, 0, 'User Fields', fmt_cols[2][0])
        if hl_empty:
            worksheet.write_string(3, 0, 'Empty Fields', fmt_cols[3][0])
        worksheet.set_column(0, 0, 50)


def adjust_widths(worksheet, column_widths, max_width):
    for i, width in enumerate(column_widths):
        if width > max_width:
            width = max_width
        worksheet.set_column(i, i, width)


def adjust_heights(worksheet, rows, max_width, head_size):
    for rn, r in enumerate(rows):
        max_h = 1
        for c in r:
            if len(c) > max_width:
                h = len(wrap(c, max_width))
                max_h = max(h, max_h)
        if max_h > 1:
            worksheet.set_row(head_size+rn, 15.0*max_h)


def write_xlsx(filename, groups, col_fields, head_names, cfg):
    """
    Write BoM out to a XLSX file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    col_fields = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    if not XLSX_SUPPORT:
        logger.error('Python xlsxwriter module not installed (Debian: python3-xlsxwriter)')
        return False

    link_datasheet = -1
    if cfg.xlsx.datasheet_as_link and cfg.xlsx.datasheet_as_link in col_fields:
        link_datasheet = col_fields.index(cfg.xlsx.datasheet_as_link)
    link_digikey = cfg.xlsx.digikey_link
    hl_empty = cfg.xlsx.highlight_empty

    workbook = Workbook(filename)
    ws_names = ['BoM', 'DNF']
    row_headings = head_names

    # Leave space for the logo, title and info
    head_size = compute_head_size(cfg)
    # First rowe for the information
    r_info_start = 1 if cfg.xlsx.title else 0
    max_width = cfg.xlsx.max_col_width

    # #######################
    # Create all the formats
    # #######################
    # Headings
    # Column names format
    fmt_head = create_fmt_head(workbook, cfg.xlsx.style)
    # Column formats
    fmt_cols = create_fmt_cols(workbook, cfg.xlsx.col_colors)
    col_fmt = create_col_fmt(col_fields, cfg.xlsx.col_colors, fmt_cols)
    # Page head
    # Logo
    image_data = get_logo_data(cfg.xlsx.logo)
    # Title
    fmt_title = create_fmt_title(workbook, cfg.xlsx.title)
    # Info
    fmt_info = create_fmt_info(workbook, cfg)

    # #######################
    # Fill the cells
    # #######################
    # Normal BoM & DNF
    for ws in range(2):
        # Second pass is DNF
        dnf = ws == 1
        # Should we generate the DNF?
        if dnf and (not cfg.xlsx.generate_dnf or cfg.n_total == cfg.n_fitted):
            break

        worksheet = workbook.add_worksheet(ws_names[ws])
        row_count = head_size

        # Headings
        # Create the head titles
        column_widths = [0]*len(col_fields)
        rows = [row_headings]
        for i in range(len(row_headings)):
            # Title for this column
            column_widths[i] = len(row_headings[i]) + 10
            worksheet.write_string(row_count, i, row_headings[i], fmt_head)

        # Body
        row_count += 1
        for i, group in enumerate(groups):
            if (cfg.ignore_dnf and not group.is_fitted()) != dnf:
                continue
            # Get the data row
            row = group.get_row(col_fields)
            rows.append(row)
            if link_datasheet != -1:
                datasheet = group.get_field(ColumnList.COL_DATASHEET_L)
            # Fill the row
            for i in range(len(row)):
                cell = row[i]
                if hl_empty and (len(cell) == 0 or cell.strip() == "~"):
                    fmt = col_fmt[-1][row_count % 2]
                else:
                    fmt = col_fmt[i][row_count % 2]
                # Link this column to the datasheet?
                if link_datasheet == i and datasheet.startswith('http'):
                    worksheet.write_url(row_count, i, datasheet, fmt, cell)
                # A link to Digi-Key?
                elif link_digikey and col_fields[i] in link_digikey:
                    url = 'http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail&name=' + cell
                    worksheet.write_url(row_count, i, url, fmt, cell)
                else:
                    worksheet.write_string(row_count, i, cell, fmt)
                if len(cell) > column_widths[i] - 5:
                    column_widths[i] = len(cell) + 5
            row_count += 1

        # Page head
        # Logo
        col1 = insert_logo(worksheet, image_data)
        # Title
        if cfg.xlsx.title:
            worksheet.set_row(0, 32)
            worksheet.merge_range(0, col1, 0, len(column_widths)-1, cfg.xlsx.title, fmt_title)
        # PCB & Stats Info
        if not (cfg.xlsx.hide_pcb_info and cfg.xlsx.hide_stats_info):
            rc = r_info_start
            if not cfg.xlsx.hide_pcb_info:
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Schematic:", cfg.source)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Variant:", ' + '.join(cfg.variant))
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Revision:", cfg.revision)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Date:", cfg.date)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "KiCad Version:", cfg.kicad_version)
                col1 += 2
            rc = r_info_start
            if not cfg.xlsx.hide_stats_info:
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Component Groups:", cfg.n_groups)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Component Count:", cfg.n_total)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Fitted Components:", cfg.n_fitted)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Number of PCBs:", cfg.number)
                rc = add_info(worksheet, column_widths, rc, col1, fmt_info, "Total Components:", cfg.n_build)

        # Adjust cols and rows
        adjust_widths(worksheet, column_widths, max_width)
        adjust_heights(worksheet, rows, max_width, head_size)

        worksheet.freeze_panes(head_size+1, 0)
        worksheet.repeat_rows(head_size+1)
        worksheet.set_landscape()

    # Add a sheet for the color references
    create_color_ref(workbook, cfg.xlsx.col_colors, hl_empty, fmt_cols)
    workbook.close()

    return True
