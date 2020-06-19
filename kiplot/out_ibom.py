import os
from subprocess import (check_output, STDOUT, CalledProcessError)
from .out_base import (BaseOutput)
from .misc import (CMD_IBOM, URL_IBOM, BOM_ERROR)
from .kiplot import (GS, check_script)
from . import log

logger = log.get_logger(__name__)


class IBoM(BaseOutput):
    def __init__(self, name, type, description):
        super(IBoM, self).__init__(name, type, description)
        self._sch_related = True
        # Options
        self.blacklist = ''
        self.name_format = ''

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


# Register it
BaseOutput.register('ibom', IBoM)
