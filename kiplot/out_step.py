import os
import re
from subprocess import (check_output, STDOUT, CalledProcessError)
from .out_base import BaseOutput
from .error import KiPlotConfigurationError
from .misc import (KICAD2STEP, KICAD2STEP_ERR)
from .kiplot import (GS)
from . import log

logger = log.get_logger(__name__)


class STEP(BaseOutput):
    def __init__(self, name, type, description):
        super(STEP, self).__init__(name, type, description)
        # Options
        self.metric_units = True
        self._origin = 'grid'
        self.no_virtual = False   # exclude 3D models for components with 'virtual' attribute
        self.min_distance = -1    # Minimum distance between points to treat them as separate ones (default 0.01 mm)
        self.output = ''

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, val):
        if (val not in ['grid', 'drill']) and (re.match(r'[-\d\.]+\s*,\s*[-\d\.]+\s*$', val) is None):
            raise KiPlotConfigurationError('Origin must be `grid` or `drill` or `X,Y`')
        self._origin = val

    def run(self, output_dir, board):
        # Output file name
        output = self.output
        if not output:
            output = os.path.splitext(os.path.basename(GS.pcb_file))[0]+'.step'
        output = os.path.abspath(os.path.join(output_dir, output))
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
        cmd.append(GS.pcb_file)
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
        logger.debug('Output from command:\n'+cmd_output.decode())


# Register it
BaseOutput.register('step', STEP)
