#!/usr/bin/python3
import os
import sys
cur_dir = os.path.dirname(os.path.abspath(__file__))
# subdir = 'strictyaml-1.0.6'
subdir = 'strictyaml'
sys.path.append(os.path.join(cur_dir, subdir))
# Depende de ruamel: python3-ruamel.yaml
# Depende de dateutil: python3-dateutil
from strictyaml import (load, Map, Str, Int, Seq, Any, Bool, Optional, MapPattern, YAMLError)
from strictyaml.exceptions import InconsistentIndentationDisallowed

schema_ver = MapPattern(Str(), Any())
# fname = 'scanner_error.yaml'
# fname = 'indent.yaml'
fname = 'test.yaml'
with open(fname) as f:
    s = f.read()
try:
    parsed = load(s, schema_ver, label=fname)
except InconsistentIndentationDisallowed as e:
    print('Use the same indentation across the file')
    print(e)
    sys.exit(1)
except YAMLError as e:
    print('YAML parsing error:')
    print(e)
    sys.exit(1)

schema = Map({"kiplot":
                 Map({"version": Int()}),  # noqa: E127
              Optional("preflight"): Map({
                 Optional("run_drc"): Bool(),  # noqa: E121
                 Optional("run_erc"): Bool(),
                 Optional("update_xml"): Bool(),
                 Optional("check_zone_fills"): Bool(),
                 Optional("ignore_unconnected"): Bool(),
              }),
              Optional("outputs"): Seq(Any())})

try:
    parsed = load(s, schema, label=fname)
except YAMLError as e:
    print('YAML parsing error:')
    print(e)
    sys.exit(1)

print(repr(parsed))
print(parsed['kiplot']['version'])
