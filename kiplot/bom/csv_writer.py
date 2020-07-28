# -*- coding: utf-8 -*-
"""
CSV Writer:
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

Generates a CSV, TSV or TXT file.
"""
import csv


def write_csv(filename, ext, groups, headings, head_names, cfg):
    """
    Write BoM out to a CSV file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    prefs = BomPref object
    """
    # Delimeter is assumed from file extension
    # Override delimiter if separator specified
    if cfg.separator:
        delimiter = cfg.separator
    else:
        if ext == "csv":
            delimiter = ","
        elif ext == "tsv" or ext == "txt":
            delimiter = "\t"

    n_groups = len(groups)
    n_total = sum([g.get_count() for g in groups])
    n_fitted = sum([g.get_count() for g in groups if g.is_fitted()])
    n_build = n_fitted * cfg.number

    with open(filename, "wt") as f:
        writer = csv.writer(f, delimiter=delimiter, lineterminator="\n")
        # Headers
        if not cfg.hide_headers:
            if cfg.number_rows:
                comp = "Component"
                comp_lc = comp.lower()
                if comp_lc in cfg.column_rename:
                    comp = cfg.column_rename[comp_lc]
                writer.writerow([comp] + head_names)
            else:
                writer.writerow(head_names)
        # Body
        count = 0
        row_count = 1
        for group in groups:
            if cfg.ignore_dnf and not group.is_fitted():
                continue
            row = group.get_row(headings)
            # Row number
            if cfg.number_rows:
                row = [str(row_count)] + row
            writer.writerow(row)
            count += group.get_count()
            row_count += 1
        # PCB info
        if not cfg.hide_pcb_info:
            # Add some blank rows
            for i in range(5):
                writer.writerow([])

            writer.writerow(["Component Groups:", n_groups])
            writer.writerow(["Component Count:", n_total])
            writer.writerow(["Fitted Components:", n_fitted])
            writer.writerow(["Number of PCBs:", cfg.number])
            writer.writerow(["Total components:", n_build])
            writer.writerow(["Schematic Revision:", cfg.revision])
            writer.writerow(["Schematic Date:", cfg.date])
            writer.writerow(["PCB Variant:", ' + '.join(cfg.variant)])
            # writer.writerow(["BoM Date:", net.getDate()]) same as Schematic
            writer.writerow(["Schematic Source:", cfg.source])
            # writer.writerow(["KiCad Version:", net.getTool()]) TODO?

    return True
