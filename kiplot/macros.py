from ast import *

def document(sentences, to_source, **kw):
    """ This macro takes literal strings and converts them into:
        _help_ID = type_hint+STRING
        where:
        ID is the first target of the last assignment.
        type_hint is the assigned type and default value (only works for a few types)
        STRING is the literal string """
    cur_attr = None
    cur_value = None
    for n in range(len(sentences)):
        s = sentences[n]
        if isinstance(s, Assign):
            cur_target = s.targets[0]
            if isinstance(cur_target, Name):
                cur_attr = cur_target.id
                is_attr = False
            elif isinstance(cur_target, Attribute):
                cur_attr = cur_target.attr
                is_attr = True
            else:
                raise TypeError
            cur_value = s.value
        elif cur_attr and isinstance(s, Expr):
            if isinstance(s.value, Str):
                # Remove starting underscore
                if cur_attr[0] == '_':
                    cur_attr = cur_attr[1:]
                # Create a _help_ID
                doc_id = '_help_'+cur_attr
                # Create the type hint for numbers, strings and booleans
                type_hint = ''
                if isinstance(cur_value, Num):
                    type_hint = '[number={}]'.format(cur_value.n)
                elif isinstance(cur_value, Str):
                    type_hint = "[string='{}']".format(cur_value.s)
                elif isinstance(cur_value, NameConstant) and isinstance(cur_value.value, bool):
                    type_hint = '[boolean={}]'.format(str(cur_value.value).lower())
                # Transform the string into an assign for _help_ID
                if is_attr:
                    cur_target = Attribute(value=Name(id='self', ctx=Load()), attr=doc_id, ctx=Store())
                else:
                    cur_target = Name(id=doc_id, ctx=Store())
                sentences[n] = Assign(targets=[cur_target], value=Str(s=type_hint+s.value.s))
    # Return the modified AST
    return sentences
