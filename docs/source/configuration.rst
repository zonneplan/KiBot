.. index::
   single: configuration

.. _configuration:

Configuration
-------------

KiBot uses a configuration file where you can specify what *outputs* to
generate and which preflight (before *launching* the outputs generation)
actions to perform. By default you’ll generate all of them, but you can
specify which ones from the command line.

The configuration file should be named using the **.kibot.yaml** suffix,
i.e. *my_project.kibot.yaml*. The format used is
`YAML <https://yaml.org/>`__. This is basically a text file with some
structure. This file can be compressed using *gzip* file format.

If you never used YAML read the following :ref:`explanation <kiplot-yaml>`.
Note that the explanation could be useful even if you know YAML.

.. toctree::
   :maxdepth: 3
   :caption: Configuration:

   configuration/quick_start
   configuration/section_order
   configuration/header
   configuration/outputs
   configuration/preflight
   configuration/global
   configuration/filters
   configuration/imports
   configuration/substitution
