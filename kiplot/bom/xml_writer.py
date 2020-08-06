# -*- coding: utf-8 -*-
"""
XML Writer:
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

Generates an XML file.
"""
from xml.etree import ElementTree
from xml.dom import minidom


def write_xml(filename, groups, headings, head_names, cfg):
    """
    Write BoM out to an XML file
    filename = path to output file (must be a .xml)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to display in the BoM file]
    cfg = BomPref object
    """
    attrib = {}
    attrib['Schematic_Source'] = cfg.source
    attrib['Schematic_Revision'] = cfg.revision
    attrib['Schematic_Date'] = cfg.date
    attrib['PCB_Variant'] = ', '.join(cfg.variant)
    # attrib['BOM_Date'] = net.getDate() same as schematic
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
