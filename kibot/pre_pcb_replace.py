# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024 Salvador E. Tropea
# Copyright (c) 2021-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: Git
    role: Find commit hash and/or date
  - from: Bash
    role: Run external commands to create replacement text
"""
from .gs import GS
from .pre_any_replace import TagReplaceBase, Base_ReplaceOptions, Base_Replace
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()


class TagReplacePCB(TagReplaceBase):
    """ Tags to be replaced for an PCB """
    def __init__(self):
        super().__init__()
        self._help_command += ".\nKIBOT_PCB_NAME variable is the name of the current PCB"


class PCB_ReplaceOptions(Base_ReplaceOptions):
    """ PCB replacement options """
    def __init__(self):
        super().__init__()
        self.replace_tags = TagReplacePCB


@pre_class
class PCB_Replace(Base_Replace):  # noqa: F821
    """ PCB Replace (**Deprecated**)
        Replaces tags in the PCB. I.e. to insert the git hash or last revision date.
        This is useful for KiCad 5, use `set_text_variables` when using KiCad 6.
        This preflight modifies the PCB. Even when a back-up is done use it carefully """
    _context = 'PCB'

    def __init__(self):
        super().__init__()
        with document:
            self.pcb_replace = PCB_ReplaceOptions
            """ [dict={}] Options for the `pcb_replace` preflight """

    def apply(self):
        o = self.pcb_replace
        if o.date_command:
            # Convert it into another replacement
            t = TagReplacePCB()
            t.tag = r'^(    |\t\t)\(date (\S+|"(?:[^"]|\\")+")\)$'
            t.command = o.date_command
            t.before = '    (date "'
            t.after = '")'
            t._relax_check = True
            o.replace_tags.append(t)
        self.replace(GS.pcb_file, o)
        # Force the schematic reload
        GS.board = None
