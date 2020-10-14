"""
Tests for the preflight options

We test:
- ERC
- DRC
  - ignore_unconnected
  - error
  - filter
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
from kibot.misc import (DRC_ERROR, ERC_ERROR, BOM_ERROR)


def test_erc_1():
    prj = 'bom'
    ctx = context.TestContext('ERC', prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'.erc')
    ctx.clean_up()


def test_erc_fail_1():
    """ Using an SCH with ERC errors """
    prj = 'fail-erc'
    ctx = context.TestContext('ERCFail1', prj, 'erc', '')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'.erc')
    ctx.clean_up()


def test_erc_fail_2():
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext('ERCFail2', prj, 'erc', '')
    ctx.run(ERC_ERROR)
    ctx.clean_up()


def test_drc_1():
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
    ctx.expect_out_file('kibot_errors.filter')
    ctx.clean_up()


def test_drc_unco():
    """ Check we can ignore unconnected nets """
    prj = 'warning-project'
    ctx = context.TestContext('DRCUnco', prj, 'drc_unco', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file('drc_result.rpt')
    ctx.clean_up()


def test_drc_error():
    """ Check we catch DRC errors """
    prj = 'warning-project'
    ctx = context.TestContext('DRCError', prj, 'drc', '')
    ctx.run(DRC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file('drc_result.rpt')
    ctx.clean_up()


def test_drc_fail():
    """ Check we dummy PCB """
    prj = 'bom_no_xml'
    ctx = context.TestContext('DRCFail', prj, 'drc', '')
    ctx.run(DRC_ERROR)
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


def test_update_xml_fail():
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext('Update_XMLFail', prj, 'update_xml', '')
    ctx.run(BOM_ERROR)
    ctx.clean_up()
