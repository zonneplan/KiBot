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
import shutil
import logging
import re
from subprocess import run, PIPE
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
from kibot.misc import (DRC_ERROR, ERC_ERROR, BOM_ERROR, CORRUPTED_PCB, CORRUPTED_SCH)


def test_erc_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'ERC', prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.clean_up()


def test_erc_fail_1(test_dir):
    """ Using an SCH with ERC errors """
    prj = 'fail-erc'
    ctx = context.TestContext(test_dir, 'ERCFail1', prj, 'erc', '')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.clean_up()


def test_erc_fail_2(test_dir):
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, 'ERCFail2', prj, 'erc', '')
    ctx.run(CORRUPTED_SCH)
    ctx.clean_up()


def test_erc_warning_1(test_dir):
    """ Using an SCH with ERC warnings """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'test_erc_warning_1', 'erc_warning/'+prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.search_err(r"WARNING:\(W058\) 1 ERC warnings detected")
    ctx.clean_up()


def test_erc_warning_2(test_dir):
    """ Using an SCH with ERC warnings as errors """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'test_erc_warning_1', 'erc_warning/'+prj, 'erc_no_w', '')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.search_err(r"ERROR:1 ERC errors detected")
    ctx.clean_up()


def test_drc_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'DRC', prj, 'drc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


def test_drc_filter(test_dir):
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, 'DRC_Filter', prj, 'drc_filter', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.expect_out_file('kibot_errors.filter')
    ctx.clean_up()


def test_drc_unco(test_dir):
    """ Check we can ignore unconnected nets """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, 'DRCUnco', prj, 'drc_unco', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


def test_drc_error(test_dir):
    """ Check we catch DRC errors """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, 'DRCError', prj, 'drc', '')
    ctx.run(DRC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


def test_drc_fail(test_dir):
    """ Check we dummy PCB """
    prj = 'bom_no_xml'
    ctx = context.TestContext(test_dir, 'DRCFail', prj, 'drc', '')
    ctx.run(CORRUPTED_PCB)
    ctx.clean_up()


def test_drc_time_out(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'test_drc_time_out', prj, 'drc_time_out', '')
    ctx.run(DRC_ERROR)
    ctx.search_err('Time out detected')
    ctx.search_err('kiauto_wait_start must be integer')
    ctx.clean_up()


def test_update_xml(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, 'Update_XML', prj, 'update_xml', '')
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


def test_update_xml_fail(test_dir):
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, 'Update_XMLFail', prj, 'update_xml', '')
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_sch_replace_1(test_dir):
    """ Tags replacements in an schematic """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, 'test_sch_replace_1', prj, 'sch_replace_1', '')
    ctx.run(extra=[])
    files = {}
    file = ctx.sch_file
    files[file] = file + '-bak'
    file = ctx.sch_file.replace('test_v5', 'deeper')
    files[file] = file + '-bak'
    file = ctx.sch_file.replace('test_v5', 'sub-sheet')
    files[file] = file + '-bak'
    for k, v in files.items():
        assert os.path.isfile(v), v
        assert os.path.getsize(v) > 0
    try:
        for k, v in files.items():
            logging.debug(k)
            cmd = ['/bin/bash', '-c', "date -d @`git log -1 --format='%at' -- " + k + "` +%Y-%m-%d_%H-%M-%S"]
            text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
            with open(k, 'rt') as f:
                c = f.read()
            m = re.search('^Date \"(.*)\"$', c, re.MULTILINE)
            logging.debug('Date: ' + text)
            assert m is not None
            assert m.group(1) == text
            if 'test_v5' in k:
                cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + k]
                text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
                m = re.search("Git hash: '(.*)'", c)
                logging.debug('Hash: ' + text)
                assert m is not None
                assert m.group(1) == text
    finally:
        for k, v in files.items():
            os.rename(v, k)
