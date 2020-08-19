# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Macros to make the output plug-ins cleaner.
"""
from .gs import GS  # noqa: F401
from ast import (Assign, Name, Attribute, Expr, Num, Str, NameConstant, Load, Store, UnaryOp, USub,
                 ClassDef, Call, ImportFrom, alias, copy_location)


def document(sentences, to_source, **kw):
    """ This macro takes literal strings and converts them into:
        _help_ID = type_hint+STRING
        where:
        ID is the first target of the last assignment.
        type_hint is the assigned type and default value (only works for a few types)
        STRING is the literal string """
    for n in range(len(sentences)):
        s = sentences[n]
        if not n:
            prev = s
            continue
        # The whole sentence is a string?
        if (isinstance(s, Expr) and isinstance(s.value, Str) and
           # and the previous is an assign
           isinstance(prev, Assign)):  # noqa: E128
            # Apply it to the first target
            target = prev.targets[0]
            value = prev.value
            # Extract its name
            # variables and attributes are supported
            if isinstance(target, Name):  # pragma: no cover
                # Note: The support for variables isn't currently used
                name = target.id
                is_attr = False
            elif isinstance(target, Attribute):
                name = target.attr
                is_attr = True
            else:
                # Just in case we put anything other than an attr/var assignment
                continue  # pragma: no cover
            # Remove starting underscore
            if name[0] == '_':
                name = name[1:]
            # Create a _help_ID
            doc_id = '_help_'+name
            # Create the type hint for numbers, strings and booleans
            type_hint = ''
            post_hint = ''
            if isinstance(value, Num):
                type_hint = '[number={}]'.format(value.n)
            elif isinstance(value, UnaryOp) and isinstance(value.operand, Num) and isinstance(value.op, USub):
                # -Num
                type_hint = '[number={}]'.format(-value.operand.n)
            elif isinstance(value, Str):
                type_hint = "[string='{}']".format(value.s)
            elif isinstance(value, NameConstant) and isinstance(value.value, bool):
                type_hint = '[boolean={}]'.format(str(value.value).lower())
            elif isinstance(value, Attribute):
                # Used for the default options. I.e. GS.def_global_option
                val = eval(to_source(value))
                if isinstance(val, bool):
                    # Not used yet
                    type_hint = '[boolean={}]'.format(str(val).lower())  # pragma: no cover
                elif isinstance(val, (int, float)):
                    # Not used yet
                    type_hint = '[number={}]'.format(val)  # pragma: no cover
                elif isinstance(val, str):
                    type_hint = "[string='{}']".format(val)
                post_hint += '. Affected by global options'
            # Transform the string into an assign for _help_ID
            if is_attr:
                target = Attribute(value=Name(id='self', ctx=Load()), attr=doc_id, ctx=Store())
            else:  # pragma: no cover
                target = Name(id=doc_id, ctx=Store())
            sentences[n] = Assign(targets=[target], value=Str(s=type_hint+s.value.s.rstrip()+post_hint))
            # Copy the line number from the original docstring
            copy_location(sentences[n], s)
        prev = s
    # Return the modified AST
    return sentences


def _do_wrap_class_register(tree, mod, base_class):
    if isinstance(tree, ClassDef):
        # Create the register call
        name = tree.name
        l_start = tree.lineno
        # Python 3.8:
        # l_end = tree.end_lineno
        # Python 3.7, this is good enough for our needs:
        l_end = l_start + 1
        reg_name = name.lower()
        # BaseOutput.register member:
        attr = Attribute(value=Name(id=base_class, ctx=Load()), attr='register', ctx=Load())
        # Function call to it passing reg_name and name
        # Put it in the last line.
        do_register = Expr(value=Call(func=attr, args=[Str(s=reg_name), Name(id=name, ctx=Load())], keywords=[]),
                           lineno=l_end, col_offset=0, end_lineno=l_end, end_col_offset=50)

        # Create the import
        # Put it in the decorator line.
        do_import = ImportFrom(module=mod, names=[alias(name=base_class, asname=None)], level=1,
                               lineno=l_start-1, col_offset=0, end_lineno=l_start-1, end_col_offset=50)

        return [do_import, tree, do_register]
    # Just in case somebody applies it to anything other than a class
    return tree  # pragma: no cover


def output_class(tree, **kw):
    """A decorator to wrap a class with:

       from .out_base import BaseOutput
       ... Class definition
       BaseOutput.register(CLASS_NAME_LOWER_STRING, CLASS_NAME)

       Allowing to register the class as an output. """
    return _do_wrap_class_register(tree, 'out_base', 'BaseOutput')


def pre_class(tree, **kw):
    """A decorator to wrap a class with:

       from .pre_base import BasePreFlight
       ... Class definition
       BasePreFlight.register(CLASS_NAME_LOWER_STRING, CLASS_NAME)

       Allowing to register the class as an output. """
    return _do_wrap_class_register(tree, 'pre_base', 'BasePreFlight')
