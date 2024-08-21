.. _LayerOptions:


LayerOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~

-  ``color`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; color>` [:ref:`string <string>`] (default: ``''``) Color used for this layer.
   KiCad 6+: don't forget the alpha channel for layers like the solder mask.
-  ``description`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; description>` [:ref:`string <string>`] (default: ``''``) A description for the layer, for documentation purposes.
   A default can be specified using the `layer_defaults` global option.
-  ``force_plot_invisible_refs_vals`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; force_plot_invisible_refs_vals>` [:ref:`boolean <boolean>`] (default: ``false``) Include references and values even when they are marked as invisible.
-  ``layer`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; layer>` [:ref:`string <string>`] (default: ``''``) Name of the layer. As you see it in KiCad.
-  ``plot_footprint_refs`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; plot_footprint_refs>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint references.
-  ``plot_footprint_values`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; plot_footprint_values>` [:ref:`boolean <boolean>`] (default: ``true``) Include the footprint values.
-  ``suffix`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; suffix>` [:ref:`string <string>`] (default: ``''``) Suffix used in file names related to this layer. Derived from the name if not specified.
   A default can be specified using the `layer_defaults` global option.
-  ``use_for_center`` :index:`: <pair: output - pcb_print - options - pages - repeat_layers; use_for_center>` [:ref:`boolean <boolean>`] (default: ``true``) Use this layer for centering purposes.
   You can invert the meaning using the `invert_use_for_center` option.

