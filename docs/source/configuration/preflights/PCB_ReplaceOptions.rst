.. _PCB_ReplaceOptions:


PCB_ReplaceOptions parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``date_command`` :index:`: <pair: preflight - pcb_replace - pcb_replace; date_command>` [:ref:`string <string>`] (default: ``''``) Command to get the date to use in the PCB.\\
   ```git log -1 --format='%as' -- "$KIBOT_PCB_NAME"```\\
   Will return the date in YYYY-MM-DD format.\\
   ```date -d @`git log -1 --format='%at' -- "$KIBOT_PCB_NAME"` +%Y-%m-%d_%H-%M-%S```\\
   Will return the date in YYYY-MM-DD_HH-MM-SS format.\\
   Important: on KiCad 6 the title block data is optional.
   This command will work only if you have a date in the PCB/Schematic.
-  ``replace_tags`` :index:`: <pair: preflight - pcb_replace - pcb_replace; replace_tags>`  [:ref:`TagReplacePCB parameters <TagReplacePCB>`] [:ref:`dict <dict>` | :ref:`list(dict) <list(dict)>`] (default: ``[]``) Tag or tags to replace.

.. toctree::
   :caption: Used dicts

   TagReplacePCB
