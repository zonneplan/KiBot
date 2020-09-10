# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import re
import os
from subprocess import (check_output, STDOUT, CalledProcessError)
from tempfile import NamedTemporaryFile
from .error import KiPlotConfigurationError
from .misc import (KICAD2STEP, KICAD2STEP_ERR)
from .gs import (GS)
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class STEPOptions(VariantOptions):
    def __init__(self):
        with document:
            self.metric_units = True
            """ use metric units instead of inches """
            self._origin = 'grid'
            """ determines the coordinates origin. Using grid the coordinates are the same as you have in the design sheet.
                The drill option uses the auxiliar reference defined by the user.
                You can define any other origin using the format 'X,Y', i.e. '3.2,-10' """
            self.no_virtual = False
            """ used to exclude 3D models for components with 'virtual' attribute """
            self.min_distance = -1
            """ the minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm) """
            self.output = GS.def_global_output
            """ name for the generated STEP file (%i='3D' %x='step') """
        super().__init__()

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, val):
        if (val not in ['grid', 'drill']) and (re.match(r'[-\d\.]+\s*,\s*[-\d\.]+\s*$', val) is None):
            raise KiPlotConfigurationError('Origin must be `grid` or `drill` or `X,Y`')
        self._origin = val

    def filter_components(self, dir):
        if not self._comps:
            return GS.pcb_file
        comps_hash = self.get_refs_hash()
        # Remove the 3D models for not fitted components
        rem_models = []
        for m in GS.board.GetModules():
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c and c.included and not c.fitted:
                models = m.Models()
                rem_m_models = []
                while not models.empty():
                    rem_m_models.append(models.pop())
                rem_models.append(rem_m_models)
        # Save the PCB to a temporal file
        with NamedTemporaryFile(mode='w', suffix='.kicad_pcb', delete=False, dir=dir) as f:
            fname = f.name
        logger.debug('Storing filtered PCB to `{}`'.format(fname))
        GS.board.Save(fname)
        # Undo the removing
        for m in GS.board.GetModules():
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c and c.included and not c.fitted:
                models = m.Models()
                restore = rem_models.pop(0)
                for model in restore:
                    models.push_front(model)
        return fname

    def run(self, output_dir, board):
        super().run(output_dir, board)
        # Output file name
        output = self.expand_filename(output_dir, self.output, '3D', 'step')
        # Make units explicit
        if self.metric_units:
            units = 'mm'
        else:
            units = 'in'
        # Base command with overwrite
        cmd = [KICAD2STEP, '-o', output, '-f']
        # Add user options
        if self.no_virtual:
            cmd.append('--no-virtual')
        if self.min_distance >= 0:
            cmd.extend(['--min-distance', "{}{}".format(self.min_distance, units)])
        if self.origin == 'drill':
            cmd.append('--drill-origin')
        elif self.origin == 'grid':
            cmd.append('--grid-origin')
        else:
            cmd.extend(['--user-origin', "{}{}".format(self.origin.replace(',', 'x'), units)])
        # The board
        board_name = self.filter_components(GS.pcb_dir)
        cmd.append(board_name)
        # Execute and inform is successful
        logger.debug('Executing: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:  # pragma: no cover
            # Current kicad2step always returns 0!!!!
            # This is why I'm excluding it from coverage
            logger.error('Failed to create Step file, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(KICAD2STEP_ERR)
        finally:
            # Remove the temporal PCB
            if board_name != GS.pcb_file:
                os.remove(board_name)
        logger.debug('Output from command:\n'+cmd_output.decode())


@output_class
class STEP(BaseOutput):  # noqa: F821
    """ STEP (ISO 10303-21 Clear Text Encoding of the Exchange Structure)
        Exports the PCB as a 3D model.
        This is the most common 3D format for exchange purposes.
        This output is what you get from the 'File/Export/STEP' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = STEPOptions
            """ [dict] Options for the `step` output """
