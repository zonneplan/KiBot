# -*- coding: utf-8 -*-
# Copyright (c) 2015 Salvador de la Puente González
# License: MIT
# Project: MCPY https://github.com/delapuente/mcpy
import ast
from .core import find_macros, expand_macros


def nop(*args, **kw):
    pass


def source_to_xcode(self, data, path, *, _optimize=-1):
    """Intercepts the source to code transformation and expand the macros
    before compiling to actual code."""
    tree = ast.parse(data)
    module_macro_bindings = find_macros(tree, self.name)
    expansion = expand_macros(tree, bindings=module_macro_bindings)
    return compile(expansion, path, 'exec', dont_inherit=True,
                   optimize=_optimize)
