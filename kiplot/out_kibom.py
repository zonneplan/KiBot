import os
from glob import (glob)
from subprocess import (check_output, STDOUT, CalledProcessError)
from .out_base import (BaseOutput)
from .error import KiPlotConfigurationError
from .misc import (CMD_KIBOM, URL_KIBOM, BOM_ERROR)
from .kiplot import (GS, check_script)
from kiplot.macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class KiBoM(BaseOutput):
    """ KiBoM (KiCad Bill of Materials)
        Used to generate the BoM in HTML or CSV format using the KiBoM plug-in.
        For more information: https://github.com/INTI-CMNB/KiBoM
        This output is what you get from the 'Tools/Generate Bill of Materials' menu in eeschema. """
    def __init__(self, name, type, description):
        super(KiBoM, self).__init__(name, type, description)
        self._sch_related = True
        # Options
        with document:
            self._format = 'HTML'
            """  can be HTML or CSV. """

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, val):
        if val not in ['HTML', 'CSV']:
            raise KiPlotConfigurationError("`format` must be either `HTML` or `CSV`")
        self._format = val

    def run(self, output_dir, board):
        check_script(CMD_KIBOM, URL_KIBOM)
        format = self.format.lower()
        prj = os.path.splitext(os.path.relpath(GS.pcb_file))[0]
        logger.debug('Doing BoM, format '+format+' prj: '+prj)
        cmd = [CMD_KIBOM, prj+'.xml', os.path.join(output_dir, os.path.basename(prj))+'.'+format]
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:
            logger.error('Failed to create BoM, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(BOM_ERROR)
        prj = os.path.basename(prj)
        for f in glob(os.path.join(output_dir, prj)+'*.tmp'):
            os.remove(f)
        logger.debug('Output from command:\n'+cmd_output.decode())


# Register it
BaseOutput.register('kibom', KiBoM)
