"""
Tests for the KiCost output.

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import sys
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
import logging
import subprocess


OUT_DIR = 'KiCost'


def conver2csv(xlsx):
    csv = xlsx[:-4]+'csv'
    logging.debug('Converting to CSV')
    p1 = subprocess.Popen(['xlsx2csv', '--skipemptycolumns', xlsx], stdout=subprocess.PIPE)
    with open(csv, 'w') as f:
        p2 = subprocess.Popen(['egrep', '-i', '-v', r'( date|kicost|Total purchase)'], stdin=p1.stdout, stdout=f)
        p2.communicate()[0]


def check_simple(ctx, variant):
    if variant:
        variant = '_'+variant
    name = os.path.join(OUT_DIR, 'simple'+variant+'.xlsx')
    ctx.expect_out_file(name)
    xlsx = ctx.get_out_path(name)
    conver2csv(xlsx)
    ctx.compare_txt(name[:-4]+'csv')


def test_kicost_simple(test_dir):
    prj = 'kibom-variant_kicost'
    ctx = context.TestContextSCH(test_dir, 'test_kicost_simple', prj, 'kicost_simple', OUT_DIR)
    ctx.run()
    check_simple(ctx, '')
    check_simple(ctx, 'default')
    check_simple(ctx, 'production')
    check_simple(ctx, 'test')
    ctx.clean_up()
