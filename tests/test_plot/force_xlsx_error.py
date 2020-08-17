#!/usr/bin/python
import os
import sys
# Setup the path to load local kibot module
prev_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Force the xlsxwriter module load to fail
sys.modules['xlsxwriter'] = None
# Initialize the logger
from kibot import log
log.set_domain('kibot')
logger = log.init(True, False)
logger.debug("Testing bom_writer without xlsxwriter")

# Import the module to test
from kibot.bom.bom_writer import write_bom
# Run it
write_bom('bogus', 'xlsx', [], [], {})
