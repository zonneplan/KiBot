.. index::
   single: usage
   pair: usage; command line

Usage
-----

For a quick start just go to the project’s dir and run:

.. code:: shell

   kibot --quick-start

This will generate a configuration and generate outputs. If you want to
just generate the configuration, and not the outputs, use:

.. code:: shell

   kibot --quick-start --dry

If you need a more exhaustive configuration file try:

.. code:: shell

   kibot --example

This will generate a file named ``example.kibot.yaml`` containing all
the available options and comments about them. You can use it to create
your own configuration file.

If you want to use the layers of a particular PCB in the example use:

.. code:: shell

   kibot -b PCB_FILE --example

And if you want to use the same options selected in the plot dialog use:

.. code:: shell

   kibot -b PCB_FILE -p --example

If the current directory contains only one PCB file and only one
configuration file (named \*.kibot.yaml) you can just call ``kibot``. No
arguments needed. The tool will figure out which files to use.

If more than one file is found in the current directory ``kibot`` will
use the first found and issue a warning. If you need to use other file
just tell it explicitly:

.. code:: shell

   kibot -b PCB_FILE.kicad_pcb -c CONFIG.kibot.yaml

A simple target can be added to your ``makefile``, so you can just run
``make pcb_files`` or integrate into your current build process.

.. code:: makefile

   pcb_files:
       kibot -b $(PCB) -c $(KIBOT_CFG)

If you need to suppress messages use ``--quiet`` or ``-q`` and if you
need to get more information about what’s going on use ``--verbose`` or
``-v``.

If you want to generate only some of the outputs use:

.. code:: shell

   kibot OUTPUT_1 OUTPUT_2

If you want to generate all outputs with some exceptions use:

.. code:: shell

   kibot --invert-sel OUTPUT_1 OUTPUT_2

Note that you can use the ``run_by_default`` option of the output you
want to exclude from the default runs.

If you want to skip the DRC and ERC use:

.. code:: shell

   kibot --skip-pre run_erc,run_drc

If you want to skip all the ``preflight`` tasks use:

.. code:: shell

   kibot --skip-pre all

All outputs are generated using the current directory as base. If you
want to use another directory as base use:

.. code:: shell

   kibot --out-dir OTHER_PLACE

If you want to list the available outputs defined in the configuration
file use:

.. code:: shell

   kibot --list


.. index::
   pair: usage; help

Command line help
~~~~~~~~~~~~~~~~~

.. literalinclude:: usage.txt


.. index::
   pair: usage; error levels

.. include:: errors.rst

