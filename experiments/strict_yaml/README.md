# Strict YAML

This is an experiment. The idea was: why not let the YAML parser validate the syntax? Something like a DTD.

Also: give better information for the error, like position in the file.

Looking for a solution I found [Strict YAML](https://hitchdev.com/strictyaml/). The main idea is really cool, but the implementation isn't good for users having to write a configuration file.

## Background

* I'm comparing with the current [PyYAML](https://pypi.org/project/PyYAML/) parser.
* I downloaded the sources from [PyPI](https://pypi.org/project/strictyaml/) v1.0.6.
* I then tried the code from [GitHub](https://github.com/crdoconnor/strictyaml) commit 63ceb9ba28e1e6829d0ea597ab8707863f2da1ee
* I tried to parse KiPlot's configuration files.
* The library depends on [ruamel YAML](https://pypi.org/project/ruamel.yaml/)

Test code:


```
schema_ver = MapPattern(Str(), Any())
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
                 Map({"version": Int()}),
              Optional("preflight"): Map({
                 Optional("run_drc"): Bool(),
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

```


## What I found

### Strict indentation forced, can't be disabled

I understand that detecting inconsistent indentation is a good thing. But looks too strict for my case and can't be disabled:

```
kiplot:
  version: 1

preflight:
   run_drc: true

```

Gives:

```
While parsing
  in "indent.yaml", line 5, column 4:
       run_drc: true
       ^ (line: 5)
Found mapping with indentation inconsistent with previous mapping
  in "indent.yaml", line 7, column 1:
    
    ^ (line: 7)
Nuevamente en el editor

```

Here:
- The exception can't be masked
- The message is hard to understand, line 7 doesn't even exist. The message should point to line 2.
- The `InconsistentIndentationDisallowed` is hard to import, needs:

```
from strictyaml.exceptions import InconsistentIndentationDisallowed
```

### Errors seems to be descriptive, but they are missleading

Schema:

```
schema = Map({"kiplot":
                 Map({"version": Int()}),
              Optional("preflight"): Map({
                 Optional("run_drc"): Bool(),
                 Optional("run_erc"): Bool(),
                 Optional("update_xml"): Bool(),
                 Optional("check_zone_fills"): Bool(),
                 Optional("ignore_unconnected"): Bool(),
              }),
              Optional("outputs"): Seq(Any())})
```

YAML:

```
# Example KiPlot config file
kiplot:
   version: 1

preflight:
   run_drc: true
   run_erc: true
   update_xml: true
   check_zone_fills: true
   ignore_unconnected: false

outputs:
  - name: 'gerbers'

cualquiera:
  - name: 'gerbers'

```

We get:

```
YAML parsing error:
while parsing a mapping
  in "test.yaml", line 14, column 1:
    
    ^ (line: 14)
unexpected key not in schema 'cualquiera'
  in "test.yaml", line 16, column 1:
    - name: gerbers
    ^ (line: 16)
```

While parsing an empty line? Found 'cualquiera' in line 16?

It doesn't help more than what we have:

```
Unknown section `cualquiera` in config.
```

### Parser errors are as fuzzy as the ones in PyYAML

Some errors from ruamel YAML go directly to our application:

```
preflight:
   check_zone_fills: true
    ignore_unconnected: false
```

Gives:

```
ruamel.yaml.scanner.ScannerError: mapping values are not allowed here
  in "test1.yaml", line 3, column 23:
        ignore_unconnected: false
                          ^ (line: 3)
```

This doesn't help more than:

```
mapping values are not allowed here
  in "scanner_error.yaml", line 3, column 23 
```

## Conclusion

Using it involves a lot of adaptations in the code and we:

- Don't gain better messages. They point to lines and columns, but not the right ones.
- Need to patch the library in order to make indentation checks optional.


