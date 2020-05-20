"""
Tests for the preflight options

We test:
- ERC

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context


def test_erc():
    prj = 'bom'
    ctx = context.TestContext('ERC', prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'.erc')
    # We don't have a project, and we don't want one
    os.remove(os.path.join(ctx.get_board_dir(), prj+'.pro'))
    ctx.clean_up()
