# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024 Salvador E. Tropea
# Copyright (c) 2021-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .misc import W_DEPR
from .macros import macros, pre_class  # noqa: F401
from .log import get_logger
logger = get_logger(__name__)


@pre_class
class ERC_Warnings(BasePreFlight):  # noqa: F821
    """ [boolean=false] **Deprecated**, use the `warnings_as_errors` option from `run_erc`/`erc`.
        Option for `run_erc`. ERC warnings are considered errors """
    def __init__(self, name, value):
        super().__init__(name, value)

    def config(self):
        super().config()
        logger.warning(W_DEPR+'The `erc_warnings` preflight is deprecated, use the `warnings_as_errors` option')

    def get_example():
        """ Returns a YAML value for the example config """
        return 'false'

    def apply(self):
        BasePreFlight._set_option('erc_warnings', self._enabled)  # noqa: F821
