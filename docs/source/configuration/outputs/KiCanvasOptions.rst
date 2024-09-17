.. _KiCanvasOptions:


KiCanvasOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **local_script** :index:`: <pair: output - kicanvas - options; local_script>` [:ref:`boolean <boolean>`] (default: ``true``) Download the script and use a copy.
-  **source** :index:`: <pair: output - kicanvas - options; source>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (choices: "schematic", "pcb", "project") Source to display.
-  ``controls`` :index:`: <pair: output - kicanvas - options; controls>` [:ref:`string <string>`] (default: ``'full'``) (choices: "full", "basic", "none") Which controls are displayed.
-  ``dnf_filter`` :index:`: <pair: output - kicanvas - options; dnf_filter>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to mark components as not fitted.
   A short-cut to use for simple cases where a variant is an overkill.

-  ``download`` :index:`: <pair: output - kicanvas - options; download>` [:ref:`boolean <boolean>`] (default: ``true``) Show the download button.
-  ``overlay`` :index:`: <pair: output - kicanvas - options; overlay>` [:ref:`boolean <boolean>`] (default: ``true``) Show the overlay asking to click.
-  ``pre_transform`` :index:`: <pair: output - kicanvas - options; pre_transform>` [:ref:`string <string>` | :ref:`list(string) <list(string)>`] (default: ``'_null'``) Name of the filter to transform fields before applying other filters.
   A short-cut to use for simple cases where a variant is an overkill.

-  ``title`` :index:`: <pair: output - kicanvas - options; title>` [:ref:`string <string>`] (default: ``''``) Text used to replace the sheet title. %VALUE expansions are allowed.
   If it starts with `+` the text is concatenated.
-  ``url_script`` :index:`: <pair: output - kicanvas - options; url_script>` [:ref:`string <string>`] (default: ``'https://kicanvas.org/kicanvas/kicanvas.js'``) URL for the KiCanvas script.
-  ``variant`` :index:`: <pair: output - kicanvas - options; variant>` [:ref:`string <string>`] (default: ``''``) Board variant to apply.

