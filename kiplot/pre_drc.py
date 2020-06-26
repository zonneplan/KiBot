from sys import (exit)
from subprocess import (call)
from kiplot.macros import macros, pre_class  # noqa: F401
from .error import (KiPlotConfigurationError)
from .kiplot import (GS, check_script)
from .misc import (CMD_PCBNEW_RUN_DRC, URL_PCBNEW_RUN_DRC, DRC_ERROR)
from .log import (get_logger)

logger = get_logger(__name__)


@pre_class
class Run_DRC(BasePreFlight):  # noqa: F821
    """ [boolean=false] Runs the DRC (Distance Rules Check). To ensure we have a valid PCB """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._pcb_related = True

    def run(self):
        check_script(CMD_PCBNEW_RUN_DRC, URL_PCBNEW_RUN_DRC, '1.4.0')
        cmd = [CMD_PCBNEW_RUN_DRC, 'run_drc']
        if GS.filter_file:
            cmd.extend(['-f', GS.filter_file])
        cmd.extend([GS.pcb_file, GS.out_dir])
        # If we are in verbose mode enable debug in the child
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        if BasePreFlight.get_option('ignore_unconnected'):  # noqa: F821
            cmd.insert(1, '-i')
        logger.info('- Running the DRC')
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            if ret < 0:
                logger.error('DRC errors: %d', -ret)
            else:
                logger.error('DRC returned %d', ret)
            exit(DRC_ERROR)

    def apply(self):
        pass
