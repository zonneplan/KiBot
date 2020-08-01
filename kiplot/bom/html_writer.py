# -*- coding: utf-8 -*-
"""
HTML Writer:
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

Generates a HTML file.
"""
from .columnlist import ColumnList

BG_GEN = "#E6FFEE"
BG_KICAD = "#FFE6B3"
BG_USER = "#E6F9FF"
BG_EMPTY = "#FF8080"


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


def link(text):
    for t in ["http", "https", "ftp", "www"]:
        if text.startswith(t):
            return '<a href="{t}">{t}</a>'.format(t=text)
    return text


def html_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, dnf=False):
    # Table start
    html.write('<table border="1">\n')
    # Row titles:
    html.write("<tr>\n")
    if cfg.number_rows:
        html.write("\t<th></th>\n")
    for i, h in enumerate(head_names):
        # Cell background color
        bg = bg_color(headings[i])
        html.write('\t<th align="center"{bg}>{h}</th>\n'.format(h=h, bg=' bgcolor="{}"'.format(bg) if bg else ''))
    html.write("</tr>\n")

    row_count = 0
    for i, group in enumerate(groups):
        if (cfg.ignore_dnf and not group.is_fitted()) != dnf:
            continue
        row = group.get_row(headings)
        row_count += 1
        html.write("<tr>\n")
        # Row number
        if cfg.number_rows:
            html.write('\t<td align="center">{n}</td>\n'.format(n=row_count))

        for n, r in enumerate(row):
            # A link to Digi-Key?
            if link_digikey and headings[n] in link_digikey:
                r = '<a href="http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail&name=' + r + '">' + r + '</a>'
            # Link this column to the datasheet?
            if link_datasheet and headings[n] == link_datasheet:
                r = '<a href="' + group.get_field(ColumnList.COL_DATASHEET_L) + '">' + r + '</a>'
            # Empty cell?
            if len(r) == 0 or r.strip() == "~":
                bg = BG_EMPTY
            else:
                bg = bg_color(headings[n])
            html.write('\t<td align="center"{bg}>{val}</td>\n'.format(bg=' bgcolor={}'.format(bg) if bg else '', val=link(r)))
        html.write("</tr>\n")
    html.write("</table>\n")
    return row_count


def write_html(filename, groups, headings, head_names, cfg):
    """
    Write BoM out to a HTML file
    filename = path to output file (must be a .htm or .html file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    prefs = BomPref object
    """
    link_datasheet = cfg.datasheet_as_link
    link_digikey = None
    if cfg.digikey_link:
        # TODO avoid convert
        link_digikey = cfg.digikey_link.split("\t")

    with open(filename, "w") as html:
        # HTML Header
        html.write("<html>\n")
        html.write("<head>\n")
        html.write('\t<meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        html.write("</head>\n")
        html.write("<body>\n")
        # PCB info
        if not cfg.hide_headers:
            html.write("<h2>KiBoM PCB Bill of Materials</h2>\n")
        if not cfg.hide_pcb_info:
            html.write('<table border="1">\n')
            html.write("<tr><td>Source File</td><td>{}</td></tr>\n".format(cfg.source))
            # html.write("<tr><td>BoM Date</td><td>{date}</td></tr>\n".format(date=cfg.date)) Same as schematic
            html.write("<tr><td>Schematic Revision</td><td>{}</td></tr>\n".format(cfg.revision))
            html.write("<tr><td>Schematic Date</td><td>{}</td></tr>\n".format(cfg.date))
            html.write("<tr><td>PCB Variant</td><td>{}</td></tr>\n".format(', '.join(cfg.variant)))
            # html.write("<tr><td>KiCad Version</td><td>{version}</td></tr>\n".format(version=net.getTool()))  TODO?
            html.write("<tr><td>Component Groups</td><td>{}</td></tr>\n".format(cfg.n_groups))
            html.write("<tr><td>Component Count (per PCB)</td><td>{}</td></tr>\n".format(cfg.n_total))
            html.write("<tr><td>Fitted Components (per PCB)</td><td>{}</td></tr>\n".format(cfg.n_fitted))
            html.write("<tr><td>Number of PCBs</td><td>{}</td></tr>\n".format(cfg.number))
            html.write("<tr><td>Total Component Count<br>(for {n} PCBs)</td><td>{t}</td></tr>\n".
                       format(n=cfg.number, t=cfg.n_build))
            html.write("</table>\n")
            html.write("<br>\n")

        if not cfg.hide_headers:
            html.write("<h2>Component Groups</h2>\n")
            html.write('<p style="background-color: {bg}">KiCad Fields (default)</p>\n'.format(bg=BG_KICAD))
            html.write('<p style="background-color: {bg}">Generated Fields</p>\n'.format(bg=BG_GEN))
            html.write('<p style="background-color: {bg}">User Fields</p>\n'.format(bg=BG_USER))
            html.write('<p style="background-color: {bg}">Empty Fields</p>\n'.format(bg=BG_EMPTY))

        # Fitted groups
        row_count = html_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey)

        html.write("<br><br>\n")

        if cfg.html_generate_dnf and row_count != len(groups):
            html.write("<h2>Optional components (DNF=Do Not Fit)</h2>\n")
            # DNF component groups
            html_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, True)
            html.write("<br><br>\n")

        html.write("</body></html>")

    return True
