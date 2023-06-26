#!/usr/bin/python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from kibot.bom.electro_grammar import parse

res = parse(sys.argv[1], with_extra=True, stronger=True)
print(res)
