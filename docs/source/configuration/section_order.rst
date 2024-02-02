.. index::
   pair: configuration; order
   pair: configuration; sections order

Section order
~~~~~~~~~~~~~

The file is divided in various sections. Some of them are optional.

The order in which they are declared is not relevant, they are
interpreted in the following order:

-  ``kiplot``/``kibot`` see :doc:`header`
-  ``import`` see :ref:`import-from-another`, :ref:`import-other-stuff` and :ref:`import-templates`
-  ``global`` see :doc:`global`
-  ``filters`` see :doc:`filters`
-  ``variants`` see :doc:`filters`
-  ``preflight`` see :doc:`preflight`
-  ``outputs`` see :doc:`outputs`
-  ``groups`` see :ref:`grouping-outputs`
