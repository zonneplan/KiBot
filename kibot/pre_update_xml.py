# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from sys import (exit)
from .macros import macros, pre_class  # noqa: F401
from .error import (KiPlotConfigurationError)
from .gs import (GS)
from .kiplot import check_eeschema_do, exec_with_retry
from .misc import (CMD_EESCHEMA_DO, BOM_ERROR)
from .log import (get_logger)

logger = get_logger(__name__)


@pre_class
class Update_XML(BasePreFlight):  # noqa: F821
    """ [boolean=false] Update the XML version of the BoM (Bill of Materials).
        To ensure our generated BoM is up to date.
        Note that this isn't needed when using the internal BoM generator (`bom`) """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._sch_related = True

    def run(self):
        check_eeschema_do()
        cmd = [CMD_EESCHEMA_DO, 'bom_xml', GS.sch_file, GS.out_dir]
        # If we are in verbose mode enable debug in the child
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        logger.info('- Updating BoM in XML format')
        ret = exec_with_retry(cmd)
        if ret:
            logger.error('Failed to update the BoM, error %d', ret)
            exit(BOM_ERROR)
