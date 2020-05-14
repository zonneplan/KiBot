"""
Tests of simple 2-layer PCBs.
We generate the gerbers.

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
import logging
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context


def expect_gerber_has_apertures(ctx, file, ap_list):
    ap_matches = []
    for ap in ap_list:
        # find the circular aperture for the outline
        ap_matches.append(r'%AD(.*)'+ap+r'\*%')
    grps = ctx.search_in_file(file, ap_matches)
    aps = []
    for grp in grps:
        ap_no = grp[0]
        assert ap_no is not None
        # apertures from D10 to D999
        assert len(ap_no) in [2, 3]
        aps.append(ap_no)
    logging.debug("Found apertures {}".format(aps))
    return aps


def expect_gerber_flash_at(ctx, file, pos):
    """
    Check for a gerber flash at a given point
    (it's hard to check that aperture is right without a real gerber parser
    """
    repat = r'^X{x}Y{y}D03\*$'.format(x=int(pos[0]*100000), y=int(pos[1]*100000))
    ctx.search_in_file(file, [repat])
    logging.debug("Gerber flash found: "+repat)


def test_2layer():
    prj = 'simple_2layer'
    ctx = context.TestContext('Simple_2_layer', prj, prj)
    ctx.run()

    g_dir = 'gerberdir'
    f_cu = ctx.get_gerber_filename(g_dir, 'F_Cu')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(ctx.get_gerber_job_filename(g_dir))

    expect_gerber_has_apertures(ctx, f_cu, [
        r"C,0.200000",
        r"R,2.000000X2.000000",
        r"C,1.000000"])

    # expect a flash for the square pad
    expect_gerber_flash_at(ctx, f_cu, (140, -100))

    ctx.clean_up()
