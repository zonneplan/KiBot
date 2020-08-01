# -*- coding: utf-8 -*-
"""
BoM Writer.
This code is adapted from https://github.com/SchrodingersGat/KiBoM by Oliver Henry Walters.

This is just a hub that calls the real BoM writer:
- csv_writer.py
- html_writer.py
- xml_writer.py
- xlsx_writer.py
"""
from .csv_writer import write_csv
from .html_writer import write_html
from .xml_writer import write_xml
from .xlsx_writer import write_xlsx
# from . import utils
from .. import log

logger = log.get_logger(__name__)


def write_bom(filename, ext, groups, headings, cfg):
    """
    Write BoM to file
    filename = output file path (absolute)
    groups = [list of ComponentGroup groups]
    headings = [list of fields to use as columns]
    cfg = configuration data
    """
    # Remove any headings that appear in the ignore[] list
    headings = [h for h in headings if not h.lower() in cfg.ignore]
    # Allow renaming the columns
    head_names = [h if h.lower() not in cfg.column_rename else cfg.column_rename[h.lower()] for h in headings]
    result = False
    # Some stats
    cfg.n_groups = len(groups)
    cfg.n_total = sum([g.get_count() for g in groups])
    cfg.n_fitted = sum([g.get_count() for g in groups if g.is_fitted()])
    cfg.n_build = cfg.n_fitted * cfg.number
    # CSV file writing
    if ext in ["csv", "tsv", "txt"]:
        result = write_csv(filename, ext, groups, headings, head_names, cfg)
    elif ext in ["htm", "html"]:
        result = write_html(filename, groups, headings, head_names, cfg)
    elif ext in ["xml"]:
        result = write_xml(filename, groups, headings, head_names, cfg)
    elif ext in ["xlsx"]:
        result = write_xlsx(filename, groups, headings, head_names, cfg)

    if result:
        logger.debug("{} Output -> {}".format(ext.upper(), filename))
    else:
        logger.error("writing {} output".format(ext.upper()))

    return result
