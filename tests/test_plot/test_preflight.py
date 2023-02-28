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
import json
import logging
import pytest
import os
import re
from subprocess import run, PIPE
from . import context
from kibot.misc import DRC_ERROR, ERC_ERROR, BOM_ERROR, CORRUPTED_PCB, CORRUPTED_SCH, EXIT_BAD_CONFIG, NETLIST_DIFF


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_fail_1(test_dir):
    """ Using an SCH with ERC errors """
    prj = 'fail-erc'
    ctx = context.TestContext(test_dir, prj, 'erc', '')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.clean_up()


def test_erc_fail_2(test_dir):
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'erc', '')
    ctx.run(CORRUPTED_SCH)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_warning_1(test_dir):
    """ Using an SCH with ERC warnings """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.search_err(r"WARNING:\(W058\) 1 ERC warnings detected")
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_warning_2(test_dir):
    """ Using an SCH with ERC warnings as errors """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_no_w', 'def_dir')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt', sub=True)
    ctx.search_err(r"ERROR:1 ERC errors detected")
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(not context.ki7(), reason="KiCad 7 off grid check")
def test_erc_off_grid_1(test_dir):
    """ ERC using 25 mils grid """
    prj = 'off-grid'
    ctx = context.TestContextSCH(test_dir, prj, 'erc_grid_25')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt', sub=True)
    ctx.clean_up()


def test_drc_1(test_dir):
    prj = name = 'bom'
    if context.ki7():
        prj = name = 'bom_ok_drc'
    ctx = context.TestContext(test_dir, prj, 'drc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(name+'-drc.txt')
    ctx.clean_up(keep_project=context.ki7())


def test_drc_filter_1(test_dir):
    """ Test using internal filters """
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'drc_filter', 'def_dir')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt', sub=True)
    ctx.expect_out_file('kibot_errors.filter', sub=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
@pytest.mark.skipif(context.ki5(), reason="KiCad 6 exclusions")
def test_drc_filter_2(test_dir):
    """ Test using KiCad 6 exclusions """
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'drc_filter_k6_exc', '')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.expect_out_file('kibot_errors.filter')
    ctx.clean_up(keep_project=True)


def test_drc_unco(test_dir):
    """ Check we can ignore unconnected nets """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_unco', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


def test_drc_error(test_dir):
    """ Check we catch DRC errors """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc', '')
    ctx.run(DRC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


def test_drc_fail(test_dir):
    """ Check we dummy PCB """
    prj = 'bom_no_xml'
    ctx = context.TestContext(test_dir, prj, 'drc', '')
    ctx.run(CORRUPTED_PCB)
    ctx.clean_up()


def test_drc_time_out(test_dir):
    if context.ki6():
        # KiCad 6 has Python binding, no time-out problems!
        return
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'drc_time_out', '')
    ctx.run(DRC_ERROR)
    ctx.search_err('Time out detected')
    ctx.search_err('kiauto_wait_start must be integer')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_update_xml_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'update_xml', '')
    # The XML should be created where the schematic is located
    xml = os.path.abspath(os.path.join(ctx.get_board_dir(), prj+'.xml'))
    os.replace(xml, xml+'-bak')
    try:
        ctx.run()
        # Check all outputs are there
        # ctx.expect_out_file(prj+'.csv')
        assert os.path.isfile(xml)
        assert os.path.getsize(xml) > 0
        logging.debug(os.path.basename(xml)+' OK')
    finally:
        os.remove(xml)
        os.replace(xml+'-bak', xml)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(context.ki5(), reason="KiCad 6 implementation")
def test_update_xml_2(test_dir):
    prj = 'pcb_parity'
    ctx = context.TestContext(test_dir, prj, 'update_xml_2', '')
    # The XML should be created where the schematic is located
    xml = os.path.abspath(os.path.join(ctx.get_board_dir(), prj+'.xml'))
    ctx.run(ret_val=NETLIST_DIFF)
    # Check all outputs are there
    # ctx.expect_out_file(prj+'.csv')
    assert os.path.isfile(xml)
    assert os.path.getsize(xml) > 0
    logging.debug(os.path.basename(xml)+' OK')
    ctx.search_err(["C1 footprint mismatch",
                    "F1 found in PCB, but not in schematic",
                    "FID1 found in schematic, but not in PCB",
                    "Net count mismatch .PCB 3 vs schematic 4.",
                    "PCB net code 2 name mismatch",
                    "PCB net code 2 extra connection/s: C1 pin 1"])
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_update_xml_fail(test_dir):
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'update_xml', '')
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_sch_replace_1(test_dir):
    """ Tags replacements in an schematic """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'sch_replace_1', '')
    ctx.run(extra=[])
    files = {}
    file = ctx.sch_file
    files[file] = file + '-bak'
    file = ctx.sch_file.replace('test_v5', 'deeper')
    files[file] = file + '-bak'
    file = ctx.sch_file.replace('test_v5', 'sub-sheet')
    files[file] = file + '-bak'
    for v in files.values():
        assert os.path.isfile(v), v
        assert os.path.getsize(v) > 0
    try:
        for k in files.keys():
            logging.debug(k)
            cmd = ['/bin/bash', '-c', "date -d @`git log -1 --format='%at' -- " + k + "` +%Y-%m-%d_%H-%M-%S"]
            text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
            with open(k, 'rt') as f:
                c = f.read()
            if context.ki5():
                m = re.search(r'^Date "((?:[^"]|\\")*)"$', c, re.MULTILINE)
            else:
                m = re.search(r'\(date "((?:[^"]|\\")*)"\)', c, re.MULTILINE)
            logging.debug('Date: ' + text)
            assert m is not None
            assert m.group(1) == text
            if 'test_v5' in k:
                cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + k]
                text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
                m = re.search("Git_hash:'(.*)'", c)
                logging.debug('Hash: ' + text)
                assert m is not None
                assert m.group(1) == text
    finally:
        for k, v in files.items():
            os.replace(v, k)
    ctx.clean_up()


def test_pcb_replace_1(test_dir):
    """ Tags replacements in a PCB """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'pcb_replace_1', '')
    ctx.run(extra=[])
    file = ctx.board_file
    file_back = file + '-bak'
    assert os.path.isfile(file_back), file_back
    assert os.path.getsize(file_back) > 0
    try:
        logging.debug(file)
        cmd = ['/bin/bash', '-c', "date -d @`git log -1 --format='%at' -- " + file + "` +%Y-%m-%d_%H-%M-%S"]
        text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
        with open(file, 'rt') as f:
            c = f.read()
        m = re.search(r'^    \(date (\S+|"(?:[^"]|\\")+")\)$', c, re.MULTILINE)
        logging.debug('Date: ' + text)
        assert m is not None
        assert m.group(1) == '"' + text + '"'
        cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + file]
        text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
        m = re.search("Git_hash:'(.*)'", c)
        logging.debug('Hash: ' + text)
        assert m is not None
        assert m.group(1) == text
    finally:
        os.replace(file_back, file)
    ctx.clean_up(keep_project=True)


def test_set_text_variables_1(test_dir):
    """ KiCad 6 variables """
    prj = 'test_vars'
    ctx = context.TestContextSCH(test_dir, prj, 'set_text_variables_1', '')
    if context.ki5():
        ctx.run(EXIT_BAD_CONFIG)
    else:
        ctx.run(extra_debug=True)
        file = os.path.join(ctx.get_board_dir(), ctx.board_name+context.PRO_EXT)
        file_back = file + '-bak'
        assert os.path.isfile(file_back), file_back
        assert os.path.getsize(file_back) > 0
        try:
            logging.debug(file)
            cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + ctx.sch_file]
            hash = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
            text = "Git_hash:'{}' ({})".format(hash, prj)
            with open(file, 'rt') as f:
                c = f.read()
            data = json.loads(c)
            assert 'text_variables' in data
            assert 'Comment4' in data['text_variables']
            assert data['text_variables']['Comment4'] == text
        finally:
            os.replace(file_back, file)
        ctx.expect_out_file(prj+'-bom_'+hash+'.csv')
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(context.ki5(), reason="KiCad 6 text vars (fail already tested)")
def test_set_text_variables_2(test_dir):
    """ KiCad 6 variables, test volatile changes (project restored) """
    prj = 'test_vars'
    ctx = context.TestContextSCH(test_dir, prj, 'set_text_variables_2', '')
    ctx.run()
    file = os.path.join(ctx.get_board_dir(), ctx.board_name+context.PRO_EXT)
    file_back = file + '-bak'
    assert os.path.isfile(file_back), file_back
    assert os.path.getsize(file_back) > 0
    try:
        logging.debug(file)
        cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + ctx.sch_file]
        hash = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
        with open(file, 'rt') as f:
            c = f.read()
        data = json.loads(c)
        assert 'text_variables' in data
        assert 'Comment4' not in data['text_variables']
    finally:
        os.replace(file_back, file)
    ctx.expect_out_file(prj+'-bom_'+hash+'.csv')
    ctx.clean_up(keep_project=True)
