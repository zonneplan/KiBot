# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import re
import os
from glob import glob
from subprocess import (check_output, STDOUT, CalledProcessError)
from shutil import rmtree
from .error import KiPlotConfigurationError
from .misc import KICAD2STEP, KICAD2STEP_ERR
from .gs import (GS)
from .out_base_3d import Base3DOptions, Base3D
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class STEPOptions(Base3DOptions):
    def __init__(self):
        with document:
            self.metric_units = True
            """ Use metric units instead of inches """
            self._origin = 'grid'
            """ Determines the coordinates origin. Using grid the coordinates are the same as you have in the design sheet.
                The drill option uses the auxiliary reference defined by the user.
                You can define any other origin using the format 'X,Y', i.e. '3.2,-10' """
            self.min_distance = -1
            """ The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm) """
            self.output = GS.def_global_output
            """ Name for the generated STEP file (%i='3D' %x='step') """
        # Temporal dir used to store the downloaded files
        self._tmp_dir = None
        super().__init__()
        self._expand_ext = 'step'

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, val):
        if (val not in ['grid', 'drill']) and (re.match(r'[-\d\.]+\s*,\s*[-\d\.]+\s*$', val) is None):
            raise KiPlotConfigurationError('Origin must be `grid` or `drill` or `X,Y`')
        self._origin = val

    def run(self, output):
        super().run(output)
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
        except CalledProcessError as e:
            logger.error('Failed to create Step file, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(KICAD2STEP_ERR)
        finally:
            # Remove the temporal PCB
            if board_name != GS.pcb_file:
                # KiCad likes to create project files ...
                for f in glob(board_name.replace('.kicad_pcb', '.*')):
                    os.remove(f)
            # Remove the downloaded 3D models
            if self._tmp_dir:
                rmtree(self._tmp_dir)
        logger.debug('Output from command:\n'+cmd_output.decode())


@output_class
class STEP(Base3D):  # noqa: F821
    """ STEP (ISO 10303-21 Clear Text Encoding of the Exchange Structure)
        Exports the PCB as a 3D model.
        This is the most common 3D format for exchange purposes.
        This output is what you get from the 'File/Export/STEP' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = STEPOptions
            """ [dict] Options for the `step` output """
