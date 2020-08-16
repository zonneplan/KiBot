# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
# Contributors: Geoffrey Hunter (@gbmhunter)
"""
XML Writer: Generates an XML BoM file.
"""
from xml.etree import ElementTree
from xml.dom import minidom


def write_xml(filename, groups, headings, head_names, cfg):
    """
    Write BoM out to an XML file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    attrib = {}
    attrib['Schematic_Source'] = cfg.source
    attrib['Schematic_Revision'] = cfg.revision
    attrib['Schematic_Date'] = cfg.date
    attrib['PCB_Variant'] = ', '.join(cfg.variant)
    attrib['KiCad_Version'] = cfg.kicad_version
    attrib['Component_Groups'] = str(cfg.n_groups)
    attrib['Component_Count'] = str(cfg.n_total)
    attrib['Fitted_Components'] = str(cfg.n_fitted)
    attrib['Number_of_PCBs'] = str(cfg.number)
    attrib['Total_Components'] = str(cfg.n_build)

    xml = ElementTree.Element('KiCad_BOM', attrib=attrib, encoding='utf-8')
    for group in groups:
        if cfg.ignore_dnf and not group.is_fitted():
            continue
        row = group.get_row(headings)
        attrib = {}
        for i, h in enumerate(head_names):
            # Adapt the column name to a valid XML attribute name
            h = h.replace(' ', '_')
            h = h.replace('"', '')
            h = h.replace("'", '')
            h = h.replace('#', '_num')
            attrib[h] = str(row[i])
        ElementTree.SubElement(xml, "group", attrib=attrib)

    # Most of the UTF-8 enforcement here is for Windows
    # Selecting it in the tostring  call is enough for Linux
    with open(filename, "wt", encoding="utf-8") as output:
        out = ElementTree.tostring(xml, encoding="utf-8")
        output.write(minidom.parseString(out).toprettyxml(indent="\t", encoding="utf-8").decode("utf-8"))

    return True
