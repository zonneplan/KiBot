.. index::
   pair: global options; default

Default global options
~~~~~~~~~~~~~~~~~~~~~~

The section ``global`` contains default global options that affects all
the outputs. Currently only a few option are supported.


.. index::
   pair: global options; output

Default *output* option
^^^^^^^^^^^^^^^^^^^^^^^

This option controls the default file name pattern used by all the
outputs. This makes all the file names coherent. You can always choose
the file name for a particular output.

The pattern uses the following expansions:

-  **%c** company from pcb/sch metadata.
-  **%C\ ``n``** comments line ``n`` from pcb/sch metadata.
-  **%d** pcb/sch date from metadata if available, file modification
   date otherwise.
-  **%D** date the script was started.
-  **%f** original pcb/sch file name without extension.
-  **%F** original pcb/sch file name without extension. Including the
   directory part of the name.
-  **%g** the ``file_id`` of the global variant.
-  **%G** the ``name`` of the global variant.
-  **%i** a contextual ID, depends on the output type.
-  **%I** an ID defined by the user for this output.
-  **%M** directory where the pcb/sch resides. Only the last component
   i.e. /a/b/c/name.kicad_pcb -> c
-  **%p** title from pcb/sch metadata.
-  **%r** revision from pcb/sch metadata.
-  **%S** sub-PCB name (related to multiboards).
-  **%T** time the script was started.
-  **%x** a suitable extension for the output type.
-  **%v** the ``file_id`` of the current variant, or the global variant
   if outside a variant scope.
-  **%V** the ``name`` of the current variant, or the global variant if
   outside a variant scope.

They are compatible with the ones used by IBoM. The default value for
``global.output`` is ``%f-%i%I%v.%x``. If you want to include the
revision you could add the following definition:

.. code:: yaml

   global:
     output: '%f_rev_%r-%i.%x'

Note that the following patterns: **%c**, **%C\ ``n``**, **%d**, **%f**,
**%F**, **%p** and **%r** depends on the context. If you use them for an
output related to the PCB these values will be obtained from the PCB. If
you need to force the origin of the data you can use **%bX** for the PCB
and **%sX** for the schematic, where **X** is the pattern to expand.

You can also use text variables (introduced in KiCad 6). To expand a
text variable use ``${VARIABLE}``. In addition you can also use
environment variables, defined in your OS shell or defined in the
``global`` section.


.. index::
   pair: global options; dir

Default *dir* option
^^^^^^^^^^^^^^^^^^^^

The default ``dir`` value for any output is ``.``. You can change it
here.

Expansion patterns are allowed.

Note that you can use this value as a base for output’s ``dir`` options.
In this case the value defined in the ``output`` must start with ``+``.
In this case the ``+`` is replaced by the default ``dir`` value defined
here.


.. index::
   pair: global options; variant

Default *variant* option
^^^^^^^^^^^^^^^^^^^^^^^^

This option controls the default variant applied to all the outputs.
Example:

.. code:: yaml

   global:
     variant: 'production'


.. index::
   pair: global options; units

Default *units* option
^^^^^^^^^^^^^^^^^^^^^^

This option controls the default value for the ``position`` and ``bom``
outputs. If you don’t define it then the internal defaults of each
output are applied. But when you define it the default is the defined
value.

On KiCad 6 the dimensions has units. When you create a new dimension it
uses *automatic* units. This means that KiCad uses the units currently
selected. This selection isn’t stored in the PCB file. The global
``units`` value is used by KiBot instead.


.. index::
   pair: global options; out_dir
   pair: global options; output directory

Output directory option
^^^^^^^^^^^^^^^^^^^^^^^

The ``out_dir`` option can define the base output directory. This is the
same as the ``-d``/``--out-dir`` command line option. Note that the
command line option has precedence over it.

Expansion patterns are applied to this value, but you should avoid using
patterns that expand according to the context, i.e. **%c**, **%d**,
**%f**, **%F**, **%p** and **%r**. The behavior of these patterns isn’t
fully defined in this case and the results may change in the future.

You can also use text variables (introduced in KiCad 6). To expand a
text variable use ``${VARIABLE}``. In addition you can also use
environment variables, defined in your OS shell or defined in the
``global`` section.



.. index::
   pair: global options; date_format
   pair: global options; time_format

Date format option
^^^^^^^^^^^^^^^^^^

-  The **%d**, **%sd** and **%bd** patterns use the date and time from
   the PCB and schematic. When abscent they use the file timestamp, and
   the ``date_time_format`` global option controls the format used. When
   available, and in ISO format, the ``date_format`` controls the format
   used. You can disable this reformatting assigning ``false`` to the
   ``date_reformat`` option.
-  The **%D** format is controlled by the ``date_format`` global option.
-  The **%T** format is controlled by the ``time_format`` global option.

In all cases the format is the one used by the ``strftime`` POSIX
function, for more information visit this
`site <https://strftime.org/>`__.


.. index::
   pair: global options; pcb_material
   pair: global options; solder_mask_color
   pair: global options; silk_screen_color
   pair: global options; pcb_finish
   pair: global options; PCB details

PCB details options
^^^^^^^^^^^^^^^^^^^

The following variables control the default colors and they are used for
documentation purposes:

-  ``pcb_material`` [FR4] PCB core material. Currently known are FR1 to
   FR5
-  ``solder_mask_color`` [green] Color for the solder mask. Currently
   known are green, black, white, yellow, purple, blue and red.
-  ``silk_screen_color`` [white] Color for the markings. Currently known
   are black and white.
-  ``pcb_finish`` [HAL] Finishing used to protect pads. Currently known
   are None, HAL, HASL, ENIG and ImAg.


.. index::
   pair: global options; filters
   pair: warnings (KiBot); filters

.. _filter-kibot-warnings:

Filtering KiBot warnings
^^^^^^^^^^^^^^^^^^^^^^^^

KiBot warnings are marked with ``(Wn)`` where *n* is the warning id.

Some warnings are just recommendations and you could want to avoid them
to focus on details that are more relevant to your project. In this case
you can define filters in a similar way used to :ref:`filter DRC/ERC errors <filter-drc-and-erc>`.

As an example, if you have the following warning:

::

   WARNING:(W43) Missing component `l1:FooBar`

You can create the following filter to remove it:

.. code:: yaml

   global:
     filters:
       - number: 43
         regex:  'FooBar'


.. index::
   pair: global options; supported

All available global options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: sup_globals.rst
