import os
from subprocess import (check_output, STDOUT, CalledProcessError)
from .misc import (CMD_IBOM, URL_IBOM, BOM_ERROR)
from .kiplot import (GS, check_script)
from kiplot.macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


@output_class
class IBoM(BaseOutput):  # noqa: F821
    """ IBoM (Interactive HTML BoM)
        Generates an interactive web page useful to identify the position of the components in the PCB.
        For more information: https://github.com/INTI-CMNB/InteractiveHtmlBom
        This output is what you get from the InteractiveHtmlBom plug-in (pcbnew). """
    def __init__(self, name, type, description):
        super(IBoM, self).__init__(name, type, description)
        self._sch_related = True
        # Options
        with document:
            self.blacklist = ''
            """ regular expression for the components to exclude (using the Config field) """
            self.name_format = 'ibom'
            """ format of the output name, example: %f_%r_iBoM will contain the revision and _iBoM """  # pragma: no cover

    def run(self, output_dir, board):
        check_script(CMD_IBOM, URL_IBOM)
        logger.debug('Doing Interactive BoM')
        # Tell ibom we don't want to use the screen
        os.environ['INTERACTIVE_HTML_BOM_NO_DISPLAY'] = ''
        cmd = [CMD_IBOM, GS.pcb_file, '--dest-dir', output_dir, '--no-browser', ]
        if self.blacklist:
            cmd.append('--blacklist')
            cmd.append(self.blacklist)
        if self.name_format:
            cmd.append('--name-format')
            cmd.append(self.name_format)
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:
            logger.error('Failed to create BoM, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(BOM_ERROR)
        logger.debug('Output from command:\n'+cmd_output.decode()+'\n')
