# Automagic help for attributes

## Teminology

In Python data members of a class are **attributes** and function members are **methods**.

By convention **private** attributes has names starting with underscore. Nobody enforces it, is just a convention.

## Motivation

The output classes of KiPlot are now designed as some sort of *plug-ins*. Each class defines which options are available in a clean and simple way: *Every public attribute is a valid option.*

To prevent configurations files from messing with internal machinery all the other attributes are declared *private*.

This makes things simple, you just declare public attributes and they automatically become avaliable as options.

The point is: *Can I also make their documentation simple and elegant?*.

## Docstrings

Python docstrings are a very nice feature, you just add a special string after the declaration of something and it becomes its documentation. 

The cool thing is that is part of the language, not just something an external parser collects. You can access this documentation from the code:

```
def func():
    """ func doc """
    pass

print(func.__doc__)
```

Can it solve my problem? **Nope**

Why? simple, as the above example shows the documentation is stored in an attribute. So I can't store documentation inside an attribute of an attribute ;-)

Docstrings applies to stuff that has attributes, as another attribute. It means it applies to classes, objects, modules, functions, etc. If we try to access to the docstring of a variable we will be accessing to the docstring of the object contained in the variable:

```
a = True
print(a.__doc__)
```

Prints the help for the **bool** class. The variable `a` contains a `bool` object.

## Defining another attribute

The solution can be defining another attribute with a name associated to the attribute we want to document. To avoid access from configuration files the attribute must be private. So we want to define something like *_help_NAME*. How?

### Decorators

This is another nice Python feature, you can wrap stuff with function calls. The problem could be solved if you could wrap the attribute declaration (well its first assignment) with a call to a function that takes the help text and creates the help attribute.

But **nope** again, decorators applies to classes, functions, etc. not to attributes.

### Macros

In C language we use macros to solve these situations, something like this:

```
DO_DOC(int, a, 25, "Doc for a")
```

With a propper macro that expands to:

```
int a = 25;
char *_help_a = "Doc for a";
```

What about Python? The above example is solved before compiling the C code, using a preprocessor. So you could do the same with Python. This is complex because now the scripts executed are the post-processed ones. 

Python code is "compiled" by the interpreter, not by external stages. If the idea is to keep distributing the source using a preprocessor isn't very "pythonic".

A couple of projects offer another interesting option: *syntatic macros*. The idea is to hook the Python parser to get the parsed code, expand the macros and then let Python compile the modified code.

The two projects I found are **macropy** and **mcpy**.

### macropy

The parsed code is represented in an *Abstract Syntax Tree* (aka AST). The **macropy** module hooks the Python machinery used to import modules. So you can declare functions that takes an AST, modifies it and returns the modified AST for execution.

Things are a little bit complex because:
- Only works for imported stuff, a small example needs to be imported.
- Macros are stored in separated module.

For these reasons the simplest example involves three modules. A solution for the problem we have can be found [here](https://github.com/INTI-CMNB/kiplot/tree/new_parser/experiments/__doc__/macropy)

The example (*application.py*) is:
```
from mymacros import macros, document

with document:
    # comment for a
    a = "5.1"
    """ docu a """
    b = False
    """ docu b """
    c = 3
    """ docu c """


class d(object):
    def __init__(self):
        with document:
            self.at1 = 4.5
            """ documenting d.at1 """


print("a = "+str(a)+"  # "+_help_a)
print("b = "+str(b)+"  # "+_help_b)
print("c = "+str(c)+"  # "+_help_c)
e = d()
print("e.at1 = "+str(e.at1)+"  # "+e._help_at1)
```

And its output:

```
a = 5.1  # [string='5.1'] docu a 
b = False  # [boolean=false] docu b 
c = 3  # [number=3] docu c 
e.at1 = 4.5  # [number=4.5] documenting d.at1 
```
Showing that we can simulate docstrings creating a companion variable/attribute

### mcpy

This is a simplified version of **macropy**. The module is smaller and what you need to add is also smaller.  The implementation using it can be found [here](https://github.com/INTI-CMNB/kiplot/tree/new_parser/experiments/__doc__/mcpy)

A `diff` between both implementations:

```
¤ diff -u . ../mcpy/
diff -u ./mymacros.py ../mcpy/mymacros.py
--- ./mymacros.py	2020-06-23 09:22:21.934505936 -0300
+++ ../mcpy/mymacros.py	2020-06-23 10:45:12.593827618 -0300
@@ -1,10 +1,6 @@
-from macropy.core.macros import Macros
 from ast import (Assign, Name, Attribute, Expr, Num, Str, NameConstant, Load, Store)
 
-macros = Macros()
 
-
-@macros.block
 def document(tree, **kw):
     """ This macro takes literal strings and converts them into:
         _help_ID = type_hint+STRING
diff -u ./try_mymacros.py ../mcpy/try_mymacros.py
--- ./try_mymacros.py	2020-06-23 10:44:08.773919281 -0300
+++ ../mcpy/try_mymacros.py	2020-06-23 10:44:17.413906631 -0300
@@ -1,3 +1,3 @@
 #!/usr/bin/python3
-import macropy.activate  # noqa: F401
+import mcpy.activate  # noqa: F401
 import application  # noqa: F401
```

As you can see the final *application.py* is the same.  The module implementing the macros is simpler because you don't need to mark it calling `Macros()` and you don't need to decorate the macros with `@macros.block` or similar.

### Important details

The use of these modules has some important drawbacks:

1. Error messages can become messy. Sometimes you'll get cryptic messages referencing to syntax errors on an *unknown* file.
2. The mechanism interferes with the Python cache mechanism. Recent versions of **macropy** has support for [CPython](https://github.com/python/cpython) (the official Python implementation) and [PyPy](https://www.pypy.org/). I'm not sure what's the real impact. If your code is speed sensitive you should consult the mitigation mechanisms offered by **macropy**.
3. Both packages are available from [PyPI](https://pypi.org/project/mcpy/), but neither has a Debian package. I created Debian packages for both: [macropy](https://github.com/set-soft/macropy) and [mcpy](https://github.com/set-soft/mcpy).
4. Syntactical macros are really powerful, but hard to write. **macropy** has some helpers to cover some cases, but you have to understand something about ASTs. 
5. As this looks like "magic" tools like [`flake8`](https://flake8.pycqa.org/en/latest/) won't understand what's going on and you'll need to explain. Here are some examples:
- The import to make it work (and others):
```
import macropy.activate  # noqa: F401
```
- Variable coming from nowhere:
```
print("a = "+str(a)+"  # "+_help_a)  # noqa: F821
```

