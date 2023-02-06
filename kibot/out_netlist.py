# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    command: eeschema_do
    version: 2.0.0
"""
import os
from .gs import GS
from .out_base import VariantOptions
from .misc import FAILED_EXECUTE
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class NetlistOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=netlist/IPC-D-356, %x=net/d356) """
            self.format = 'classic'
            """ *[classic,ipc] The `classic` format is the KiCad internal format, and is generated
                from the schematic. The `ipc` format is the IPC-D-356 format, useful for PCB
                testing, is generated from the PCB """
        super().__init__()
        self.help_only_sub_pcbs()

    def config(self, parent):
        super().config(parent)
        if self.format == 'classic':
            self._expand_id = 'netlist'
            self._expand_ext = 'net'
            self._category = 'PCB/export'
        else:
            self._expand_id = 'IPC-D-356'
            self._expand_ext = 'd356'
            self._category = 'PCB/fabrication/verification'

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, name):
        command = self.ensure_tool('KiAuto')
        super().run(name)
        if self.format == 'ipc':
            command = command.replace('eeschema_do', 'pcbnew_do')
            subcommand = 'ipc_netlist'
            file = self.save_tmp_board_if_variant()
        else:
            subcommand = 'netlist'
            file = GS.sch_file
        # Create the command line
        cmd = self.add_extra_options([command, subcommand, '--output_name', name, file, os.path.dirname(name)])
        # Execute it
        self.exec_with_retry(cmd, FAILED_EXECUTE)


@output_class
class Netlist(BaseOutput):  # noqa: F821
    """ Netlist
        Generates the list of connections for the project.
        The netlist can be generated in the classic format and in IPC-D-356 format,
        useful for board testing """
    def __init__(self):
        super().__init__()
        with document:
            self.options = NetlistOptions
            """ *[dict] Options for the `netlist` output """

    @staticmethod
    def get_conf_examples(name, layers, templates):
        gb1 = {}
        gb1['name'] = 'classic_'+name
        gb1['comment'] = 'Schematic netlist in KiCad format'
        gb1['type'] = name
        gb1['dir'] = 'Export'
        gb2 = {}
        gb2['name'] = 'ipc_'+name
        gb2['comment'] = 'IPC-D-356 netlist for testing'
        gb2['type'] = name
        gb2['dir'] = 'Export'
        gb2['options'] = {'format': 'ipc'}
        return [gb1, gb2]
