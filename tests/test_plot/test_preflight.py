"""
Tests for the preflight options

We test:
- ERC
- DRC
- XML update

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context


def test_erc():
    prj = 'bom'
    ctx = context.TestContext('ERC', prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'.erc')
    ctx.clean_up()


def test_drc():
    prj = 'bom'
    ctx = context.TestContext('DRC', prj, 'drc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file('drc_result.rpt')
    ctx.clean_up()


def test_drc_filter():
    prj = 'fail-project'
    ctx = context.TestContext('DRC_Filter', prj, 'drc_filter', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file('drc_result.rpt')
    ctx.expect_out_file('kiplot_errors.filter')
    ctx.clean_up()


def test_update_xml():
    prj = 'bom'
    ctx = context.TestContext('Update_XML', prj, 'update_xml', '')
    # The XML should be created where the schematic is located
    xml = os.path.abspath(os.path.join(ctx.get_board_dir(), prj+'.xml'))
    os.rename(xml, xml+'-bak')
    try:
        ctx.run()
        # Check all outputs are there
        # ctx.expect_out_file(prj+'.csv')
        assert os.path.isfile(xml)
        assert os.path.getsize(xml) > 0
        logging.debug(os.path.basename(xml)+' OK')
    finally:
        os.remove(xml)
        os.rename(xml+'-bak', xml)
    ctx.clean_up()
