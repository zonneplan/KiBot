#!/usr/bin/python3
import os
import sys
# Setup the path to load local kibot module
prev_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.path[0] != prev_dir:
    try:
        sys.path.remove(prev_dir)
    except ValueError:
        pass
    sys.path.insert(0, prev_dir)
# Force the xlsxwriter module load to fail
sys.modules['xlsxwriter'] = None
# Initialize the logger
from kibot import log
log.set_domain('kibot')
logger = log.init()
logger.debug("Testing bom_writer without xlsxwriter")

# Import the module to test
from kibot.bom.bom_writer import write_bom
from kibot.error import KiPlotError
# Run it
try:
    write_bom('bogus', 'xlsx', [], [], {})
except KiPlotError as e:
    logger.error(e)
