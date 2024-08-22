# Data types and their defaults

Outputs, filters, globals, etc. are objects derived from Optionable.
They use the `with document:` macro to create some sort of docstrings for data members.
The macros creates members called `_help_MEMBER` containing the docstring found in the code.
This docstring is used to generate the documentation but also to validate the data from the YAML config file.
This document talks about the rules used for the validation.


## Simple datatypes

The `number`, `boolean` and `string` datatypes are directly interpreted by the macros. So code like this:

```python
with document:
    self.v1 = 5
    """ A number """
    self.v2 = True
    """ A boolean """
    self.v3 = 'Hello'
    """ A string """
```

Will automagically define:

```python
self._help_v1 = "[number=5] A number"
self._help_v2 = "[boolean=true] A boolean"
self._help_v3 = "[string='Hello'] A string"
```

The type and default are automatically filled.


## Aliases

To define an alias we use:

```python
with document:
    self.posx = 10
    """ Bla bla """
    self.pos_x = None
    """ {posx} """
```

In this case the real member is `posx` but the user can use `pos_x`.


## Important (basic) parameters

When a member is very important we mark it using an asterisk:

```python
with document:
    self.posx = 10
    """ *Bla bla """
```

This asterisk goes before any datatype indication:

```python
self._help_posx = "*[number=10] Bla bla"
```


## Multiple datatypes

Some parameters can be defined using different data types, here is an example:

```python
with document:
    self.posx = 10
    """ [number|string=10] Bla bla """
```

This means that we can use a *number* or a *string* in the YAML.
Note that in this case we must explicitly indicate the valid data types and the default.


## Complex datatypes

They are *list*, *dict* and their combination, i.e.:

- dict
- list(string)
- list(dict)
- list(list(string))

To handle them we always use a class. For the simplest cases we just use *Optionable*, like this:

```python
with document:
    self.v1 = Optionable
    """ [list(string)=[]] Bla bla """
```

Here we must specify the valid data types and the default.
This example says the default is an empty list, we use *{}* for a default *dict*, the one created instantiating the class.
For *dict* and *list(dict)* we must define a class with a *__init__* that uses `with document:` to define the valid keys.


## Complex defaults

The complex datatypes might need a complex default, one that is complex to write in the help.
For this case we can leave the default undefined and define a data member *_default* in the class used for the member.


## Unknown defaults

When the default will be created on-the-fly we use *?* for its value.


## Number ranges

They are specified using *[min,max]*, like this:

```python
with document:
    self.texture_dpi = 1016.0
    """ [508,2032] Texture density in dots per inch """
    self.xxx = 20
    """ [number|string=20] [1,100] Bla bla """
```


## Choices

They are specified using *[OPS1,OPS2,OPS3]*, like this:


```python
with document:
    self.solder_joints = "SMART"
    """ [NONE,SMART,ALL] The plug-in can add nice looking solder joints """
```


## Extended choices

When we can also enter an arbitrary value we use an asterisk as the last option:

```python
with document:
    self.solder_joints = "SMART"
    """ [NONE,SMART,ALL,*] The plug-in can add nice looking solder joints """
```

## Random notes

We edit the data from the YAML tree, but we also use the data from the actually created objects for things that aren't in the tree.

Why not just the defaults?

The classes are free to fill things from the data to fill the gaps.
