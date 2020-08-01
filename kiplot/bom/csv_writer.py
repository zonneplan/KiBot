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

    with open(filename, "wt") as f:
        writer = csv.writer(f, delimiter=delimiter, lineterminator="\n")
        # Headers
        if not cfg.hide_headers:
            writer.writerow(head_names)
        # Body
        for group in groups:
            if cfg.ignore_dnf and not group.is_fitted():
                continue
            row = group.get_row(headings)
            writer.writerow(row)
        # PCB info
        if not cfg.hide_pcb_info:
            # Add some blank rows
            for i in range(5):
                writer.writerow([])
            # The info
            writer.writerow(["Component Groups:", cfg.n_groups])
            writer.writerow(["Component Count:", cfg.n_total])
            writer.writerow(["Fitted Components:", cfg.n_fitted])
            writer.writerow(["Number of PCBs:", cfg.number])
            writer.writerow(["Total components:", cfg.n_build])
            writer.writerow(["Schematic Revision:", cfg.revision])
            writer.writerow(["Schematic Date:", cfg.date])
            writer.writerow(["PCB Variant:", ' + '.join(cfg.variant)])
            # writer.writerow(["BoM Date:", net.getDate()]) same as Schematic
            writer.writerow(["Schematic Source:", cfg.source])
            # writer.writerow(["KiCad Version:", net.getTool()]) TODO?

    return True
