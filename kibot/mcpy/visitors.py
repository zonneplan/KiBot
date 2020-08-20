# -*- coding: utf-8 -*-
# Copyright (c) 2015 Salvador de la Puente González
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: MIT
# Project: MCPY https://github.com/delapuente/mcpy
from ast import NodeTransformer, AST, copy_location, fix_missing_locations, Call, Constant, Name, Expr, Load
from .unparse import unparse


class BaseMacroExpander(NodeTransformer):
    """
    A base class for macro expander visitors. After identifying valid macro
    syntax, the actual expander should return the result of calling `_expand()`
    method with the proper arguments.
    """

    def __init__(self, bindings):
        self.bindings = bindings

    def visit(self, tree):
        """Short-circuit visit() to avoid expansions if no macros."""
        return super().visit(tree) if self.bindings else tree

    def _expand(self, syntax, target, macroname, tree, kw=None):
        """
        Transform `target` node, replacing it with the expansion result of
        aplying the named macro on the proper node and recursively treat the
        expansion as well.
        """
        macro = self.bindings[macroname]
        kw = kw or {}
        kw.update({
            'syntax': syntax,
            'to_source': unparse,
            'expand_macros': self.visit
        })
        expansion = _apply_macro(macro, tree, kw)

        if syntax == 'block':
            # I'm not sure why is all this mess
            #
            # Strategy 1: Make the last line cover the whole block.
            # Result: Covers the "with document" line, but not the last one.
            # copy_location(expansion[-1], target)
            #
            # Strategy 2: Make the second line cover the whole block.
            # Result: Covers all, unless the block is just 2 lines.
            # copy_location(expansion[1], target) # Lo mejor para largo > 2
            #
            # Strategy 3: Insert a second dummy line covering the whole block.
            # Result: Works
            dummy = Expr(value=Call(func=Name(id="id", ctx=Load()), args=[Constant(value="bogus", kind=None)], keywords=[]),
                         lineno=target.lineno)
            copy_location(dummy, target)
            expansion.insert(1, dummy)
        expansion = self._visit_expansion(expansion, target)
        return expansion

    def _visit_expansion(self, expansion, target):
        """
        Ensures the macro expansions into None (deletions), other nodes or
        list of nodes are expanded too.
        """
        if expansion is not None:
            is_node = isinstance(expansion, AST)
            expansion = [expansion] if is_node else expansion
            # The following is nice when we don't put any effort in filling lineno, but then is impossible to get a
            # rasonable coverage. So now I'm disabling it and doing some extra effort to indicate where is the code.
            # expansion = map(lambda n: copy_location(n, target), expansion)
            # The following fills the gaps
            expansion = map(fix_missing_locations, expansion)
            expansion = map(self.visit, expansion)
            expansion = list(expansion).pop() if is_node else list(expansion)

        return expansion

    def _ismacro(self, name):
        return name in self.bindings


def _apply_macro(macro, tree, kw):
    """ Executes the macro on tree passing extra kwargs. """
    return macro(tree, **kw)
