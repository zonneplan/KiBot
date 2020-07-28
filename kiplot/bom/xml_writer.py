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
    n_groups = len(groups)
    n_total = sum([g.get_count() for g in groups])
    n_fitted = sum([g.get_count() for g in groups if g.is_fitted()])
    n_build = n_fitted * cfg.number

    attrib = {}
    attrib['Schematic_Source'] = cfg.source
    attrib['Schematic_Revision'] = cfg.revision
    attrib['Schematic_Date'] = cfg.date
    attrib['PCB_Variant'] = ', '.join(cfg.variant)
    # attrib['BOM_Date'] = net.getDate() same as schematic
    # attrib['KiCad_Version'] = net.getTool()  TODO?
    attrib['Component_Groups'] = str(n_groups)
    attrib['Component_Count'] = str(n_total)
    attrib['Fitted_Components'] = str(n_fitted)
    attrib['Number_of_PCBs'] = str(cfg.number)
    attrib['Total_Components'] = str(n_build)

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

    with open(filename, "wt") as output:
        out = ElementTree.tostring(xml, encoding="utf-8")
        output.write(minidom.parseString(out).toprettyxml(indent="\t"))

    return True
