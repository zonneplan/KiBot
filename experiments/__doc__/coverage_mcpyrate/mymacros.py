from ast import (Assign, Name, Attribute, Expr, Num, Str, NameConstant, Load, Store, copy_location)


def document(tree, **kw):
    """ This macro takes literal strings and converts them into:
        _help_ID = type_hint+STRING
        where:
        ID is the first target of the last assignment.
        type_hint is the assigned type and default value (only works for a few types)
        STRING is the literal string """
    # Simplify it just to show the problem isn't related to the content of the macro
    # Note: This triggers another issue, Expr nodes can be optimized out if not assigned to a target
    # return tree
    for n in range(len(tree)):
        s = tree[n]
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
            if isinstance(target, Name):
                name = target.id
                is_attr = False
            elif isinstance(target, Attribute):
                name = target.attr
                is_attr = True
            # Create a _help_ID
            doc_id = '_help_'+name
            # Create the type hint for numbers, strings and booleans
            type_hint = ''
            if isinstance(value, Num):
                type_hint = '[number={}]'.format(value.n)
            elif isinstance(value, Str):
                type_hint = "[string='{}']".format(value.s)
            elif isinstance(value, NameConstant) and isinstance(value.value, bool):
                type_hint = '[boolean={}]'.format(str(value.value).lower())
            # Transform the string into an assign for _help_ID
            if is_attr:
                target = Attribute(value=Name(id='self', ctx=Load()), attr=doc_id, ctx=Store())
            else:
                target = Name(id=doc_id, ctx=Store())
            help_str = s.value
            help_str.s = type_hint+s.value.s
            tree[n] = Assign(targets=[target], value=help_str)
            # Copy the line number from the original docstring
            copy_location(target, s)
            copy_location(tree[n], s)
        prev = s
    # Return the modified AST
    return tree
