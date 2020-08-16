# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
"""
CSV Writer: Generates a CSV, TSV or TXT BoM file.
"""
import csv


def write_csv(filename, ext, groups, headings, head_names, cfg):
    """
    Write BoM out to a CSV file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    # Delimeter is assumed from file extension
    # Override delimiter if separator specified
    if ext == "csv" and cfg.csv.separator:
        delimiter = cfg.csv.separator
    else:
        if ext == "csv":
            delimiter = ","
        elif ext == "tsv" or ext == "txt":
            delimiter = "\t"

    if cfg.csv.quote_all:
        quoting = csv.QUOTE_ALL
    else:
        quoting = csv.QUOTE_MINIMAL
    with open(filename, "wt") as f:
        writer = csv.writer(f, delimiter=delimiter, lineterminator="\n", quoting=quoting)
        # Headers
        writer.writerow(head_names)
        # Body
        for group in groups:
            if cfg.ignore_dnf and not group.is_fitted():
                continue
            row = group.get_row(headings)
            writer.writerow(row)
        # PCB info
        if not (cfg.csv.hide_pcb_info and cfg.csv.hide_stats_info):
            # Add some blank rows
            for i in range(5):
                writer.writerow([])
            # The info
            if not cfg.csv.hide_pcb_info:
                writer.writerow(["Project info:"])
                writer.writerow(["Schematic:", cfg.source])
                writer.writerow(["Variant:", ' + '.join(cfg.variant)])
                writer.writerow(["Revision:", cfg.revision])
                writer.writerow(["Date:", cfg.date])
                writer.writerow(["KiCad Version:", cfg.kicad_version])
            if not cfg.csv.hide_stats_info:
                writer.writerow(["Statistics:"])
                writer.writerow(["Component Groups:", cfg.n_groups])
                writer.writerow(["Component Count:", cfg.n_total])
                writer.writerow(["Fitted Components:", cfg.n_fitted])
                writer.writerow(["Number of PCBs:", cfg.number])
                writer.writerow(["Total Components:", cfg.n_build])

    return True
