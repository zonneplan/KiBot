import os
import sys

# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context   # noqa: F401
prev_dir = os.path.dirname(prev_dir)
# py-test inserts things at the beginning, so we could end loading an installed copy of KiBot
if sys.path[0] != prev_dir:
    try:
        sys.path.remove(prev_dir)
    except ValueError:
        pass
    sys.path.insert(0, prev_dir)
