# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
"""
HTML Writer: Generates a HTML BoM file.
"""
import os
from base64 import b64encode
from struct import unpack
from .columnlist import ColumnList, BoMError
from .kibot_logo import KIBOT_LOGO, KIBOT_LOGO_W, KIBOT_LOGO_H

BG_GEN = "#E6FFEE"
BG_KICAD = "#FFE6B3"
BG_USER = "#E6F9FF"
BG_EMPTY = "#FF8080"
BG_GEN_L = "#F0FFF4"
BG_KICAD_L = "#FFF0BD"
BG_USER_L = "#F0FFFF"
BG_EMPTY_L = "#FF8A8A"
HEAD_COLOR_R = "#982020"
HEAD_COLOR_G = "#009879"
HEAD_COLOR_B = "#0e4e8e"
STYLE_COMMON = (" .cell-title { vertical-align: bottom; }\n"
                " .cell-info { vertical-align: top; padding: 1em;}\n"
                " .cell-stats { vertical-align: top; padding: 1em;}\n"
                " .title { font-size:2.5em; font-weight: bold; }\n"
                " .h2 { font-size:1.5em; font-weight: bold; }\n"
                " .td-empty0 { text-align: center; background-color: "+BG_EMPTY+";}\n"
                " .td-gen0 { text-align: center; background-color: "+BG_GEN+";}\n"
                " .td-kicad0 { text-align: center; background-color: "+BG_KICAD+";}\n"
                " .td-user0 { text-align: center; background-color: "+BG_USER+";}\n"
                " .td-empty1 { text-align: center; background-color: "+BG_EMPTY_L+";}\n"
                " .td-gen1 { text-align: center; background-color: "+BG_GEN_L+";}\n"
                " .td-kicad1 { text-align: center; background-color: "+BG_KICAD_L+";}\n"
                " .td-user1 { text-align: center; background-color: "+BG_USER_L+";}\n"
                " .color-ref { margin: 25px 0; }\n"
                " .color-ref th { text-align: left }\n"
                " .color-ref td { padding: 5px 20px; }\n"
                " .head-table { margin-bottom: 2em; }\n")
TABLE_MODERN = """
 .content-table {
   border-collapse:
   collapse;
   margin-top: 5px;
   margin-bottom: 4em;
   font-size: 0.9em;
   font-family: sans-serif;
   min-width: 400px;
   border-radius: 5px 5px 0 0;
   overflow: hidden;
   box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
 }
 .content-table thead tr { background-color: @bg@; color: #ffffff; text-align: left; }
 .content-table th, .content-table td { padding: 12px 15px; }
 .content-table tbody tr { border-bottom: 1px solid #dddddd; }
 .content-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
 .content-table tbody tr:last-of-type { border-bottom: 2px solid @bg@; }
"""
TABLE_CLASSIC = " .content-table, .content-table th, .content-table td { border: 1px solid black; }\n"


def cell_class(col):
    """ Return a background color for a given column title """
    col = col.lower()
    # Auto-generated columns
    if col in ColumnList.COLUMNS_GEN_L:
        return 'gen'  # BG_GEN
    # KiCad protected columns
    elif col in ColumnList.COLUMNS_PROTECTED_L:
        return 'kicad'  # BG_KICAD
    # Additional user columns
    return 'user'  # BG_USER


def link(text):
    for t in ["http", "https", "ftp", "www"]:
        if text.startswith(t):
            return '<a href="{t}">{t}</a>'.format(t=text)
    return text


def content_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, col_colors, dnf=False):
    cl = ''
    # Table start
    html.write('<table class="content-table">\n')
    # Row titles:
    html.write(" <thead>\n")
    html.write("  <tr>\n")
    for i, h in enumerate(head_names):
        if col_colors:
            # Cell background color
            cl = ' class="th-'+cell_class(headings[i])+'"'
        html.write('   <th{}>{}</th>\n'.format(cl, h))
    html.write("  </tr>\n")
    html.write(" </thead>\n")

    html.write(" <tbody>\n")
    rc = 0
    hl_empty = cfg.html.highlight_empty
    for i, group in enumerate(groups):
        if (cfg.ignore_dnf and not group.is_fitted()) != dnf:
            continue
        row = group.get_row(headings)
        if link_datasheet != -1:
            datasheet = group.get_field(ColumnList.COL_DATASHEET_L)
        html.write("  <tr>\n")
        for n, r in enumerate(row):
            # A link to Digi-Key?
            if link_digikey and headings[n] in link_digikey:
                r = '<a href="http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail&name=' + r + '">' + r + '</a>'
            # Link this column to the datasheet?
            if link_datasheet == n and datasheet.startswith('http'):
                r = '<a href="' + datasheet + '">' + r + '</a>'
            if col_colors:
                # Empty cell?
                if hl_empty and (len(r) == 0 or r.strip() == "~"):
                    cl = 'empty'
                else:
                    cl = cell_class(headings[n])
                cl = ' class="td-{}{}"'.format(cl, rc % 2)
            html.write('   <td{}>{}</td>\n'.format(cl, link(r)))
        html.write("  </tr>\n")
        rc += 1
    html.write(" </tbody>\n")
    html.write("</table>\n")
    return


def embed_image(file):
    with open(file, 'rb') as f:
        s = f.read()
    if not (s[:8] == b'\x89PNG\r\n\x1a\n' and (s[12:16] == b'IHDR')):
        raise BoMError('Only PNG images are supported for the logo')
    w, h = unpack('>LL', s[16:24])
    return int(w), int(h), 'data:image/png;base64,'+b64encode(s).decode('ascii')


def write_html(filename, groups, headings, head_names, cfg):
    """
    Write BoM out to a HTML file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    link_datasheet = -1
    if cfg.html.datasheet_as_link and cfg.html.datasheet_as_link in headings:
        link_datasheet = headings.index(cfg.html.datasheet_as_link)
    link_digikey = cfg.html.digikey_link
    col_colors = cfg.html.col_colors
    # Compute the CSS
    style_name = cfg.html.style
    if os.path.isfile(style_name):
        with open(style_name, 'rt') as f:
            style = f.read()
    else:
        # Common stuff
        style = STYLE_COMMON
        if style_name.startswith('modern-'):
            # content-table details
            if style_name.endswith('green'):
                head_color = HEAD_COLOR_G
            elif style_name.endswith('blue'):
                head_color = HEAD_COLOR_B
            else:
                head_color = HEAD_COLOR_R
            style += TABLE_MODERN.replace('@bg@', head_color)
        else:
            style += TABLE_CLASSIC

    with open(filename, "w") as html:
        # HTML Head
        html.write("<html>\n")
        html.write("<head>\n")
        html.write(' <meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        if cfg.html.title:
            html.write(' <title>'+cfg.html.title+'</title>\n')
        # CSS
        html.write("<style>\n")
        html.write(style)
        html.write("</style>\n")
        html.write("</head>\n")

        html.write("<body>\n")
        # Page Header
        img = None
        if cfg.html.logo is not None:
            if cfg.html.logo:
                img_w, img_h, img = embed_image(cfg.html.logo)
            else:
                img = 'data:image/png;base64,'+KIBOT_LOGO
                img_w = KIBOT_LOGO_W
                img_h = KIBOT_LOGO_H
        if img or not cfg.html.hide_pcb_info or not cfg.html.hide_stats_info or cfg.html.title:
            html.write('<table class="head-table">\n')
            html.write('<tr>\n')
            html.write(' <td rowspan="2">\n')
            if img:
                html.write('  <img src="'+img+'" alt="Logo" width="'+str(img_w)+'" height="'+str(img_h)+'">\n')
            html.write(' </td>\n')
            html.write(' <td colspan="2" class="cell-title">\n')
            if cfg.html.title:
                html.write('  <div class="title">'+cfg.html.title+'</div>\n')
            html.write(' </td>\n')
            html.write('</tr>\n')
            html.write('<tr>\n')
            html.write(' <td class="cell-info">\n')
            if not cfg.html.hide_pcb_info:
                html.write("   <b>Schematic</b>: {}<br>\n".format(cfg.source))
                html.write("   <b>Variant</b>: {}<br>\n".format(', '.join(cfg.variant)))
                html.write("   <b>Revision</b>: {}<br>\n".format(cfg.revision))
                html.write("   <b>Date</b>: {}<br>\n".format(cfg.date))
                html.write("   <b>KiCad Version</b>: {}<br>\n".format(cfg.kicad_version))
            html.write(' </td>\n')
            html.write(' <td class="cell-stats">\n')
            if not cfg.html.hide_stats_info:
                html.write("   <b>Component Groups</b>: {}<br>\n".format(cfg.n_groups))
                html.write("   <b>Component Count</b>: {} (per PCB)<br>\n\n".format(cfg.n_total))
                html.write("   <b>Fitted Components</b>: {} (per PCB)<br>\n".format(cfg.n_fitted))
                html.write("   <b>Number of PCBs</b>: {}<br>\n".format(cfg.number))
                html.write("   <b>Total Components</b>: {t} (for {n} PCBs)<br>\n".format(n=cfg.number, t=cfg.n_build))
            html.write(' </td>\n')
            html.write('</tr>\n')
            html.write('</table>\n')

        # Fitted groups
        html.write("<h2>Component Groups</h2>\n")
        content_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, col_colors)

        # DNF component groups
        if cfg.html.generate_dnf and cfg.n_total != cfg.n_fitted:
            html.write("<h2>Optional components (DNF=Do Not Fit)</h2>\n")
            content_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, col_colors, True)

        # Color reference
        if col_colors:
            html.write('<table class="color-ref">\n')
            html.write('<tr><th>Color reference:</th></tr>\n')
            html.write('<tr><td class="td-kicad0">KiCad Fields (default)</td></tr>\n')
            html.write('<tr><td class="td-gen0">Generated Fields</td></tr>\n')
            html.write('<tr><td class="td-user0">User Fields</td></tr>\n')
            if cfg.html.highlight_empty:
                html.write('<tr><td class="td-empty0">Empty Fields</td></tr>\n')
            html.write('</table>\n')

        html.write("</body></html>")

    return True
