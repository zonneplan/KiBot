import os
from subprocess import (call)
from .out_base import BaseOutput
from .kiplot import (check_eeschema_do, GS)
from .misc import (CMD_EESCHEMA_DO, PDF_SCH_PRINT)
from . import log

logger = log.get_logger(__name__)


class PDFSchPrint(BaseOutput):
    def __init__(self, name, type, description):
        super(PDFSchPrint, self).__init__(name, type, description)
        self._sch_related = True
        # Options
        self.output = ''

    def run(self, output_dir, board):
        check_eeschema_do()
        cmd = [CMD_EESCHEMA_DO, 'export', '--all_pages', '--file_format', 'pdf', GS.sch_file, output_dir]
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            logger.error(CMD_EESCHEMA_DO+' returned %d', ret)
            exit(PDF_SCH_PRINT)
        if self.output:
            cur = os.path.abspath(os.path.join(output_dir, os.path.splitext(os.path.basename(GS.pcb_file))[0]) + '.pdf')
            new = os.path.abspath(os.path.join(output_dir, self.output))
            logger.debug('Moving '+cur+' -> '+new)
            os.rename(cur, new)


# Register it
BaseOutput.register('pdf_sch_print', PDFSchPrint)
