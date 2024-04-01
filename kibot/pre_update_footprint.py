# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .gs import GS
from .error import KiPlotConfigurationError
from .kicad.config import KiConf
from .kicad.sexpdata import Symbol, sexp_iter
from .kicad.sexp_helpers import _check_relaxed, _get_symbol_name, save_pcb_from_sexp, load_sexp_file
from .misc import W_NOLIB
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)
# Attributes that we don't change for KiCad 6/7 (tedit is for KiCad 6)
KICAD6_ATTRS = {'layer', 'tedit', 'tstamp', 'at', 'path', 'fp_text'}
# Same for KiCad 8
KICAD8_ATTRS = {'layer', 'uuid', 'at', 'property'}


def keep_attr(names, sexp):
    return not isinstance(sexp, list) or len(sexp) < 2 or not isinstance(sexp[0], Symbol) or sexp[0].value() in names


@pre_class
class Update_Footprint(BasePreFlight):  # noqa: F821
    """ [string|list(string)=''] Updates footprints from the libs, you must provide one or more references to be updated.
        This is useful to replace logos using freshly created versions """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, list) and not isinstance(value, str):
            raise KiPlotConfigurationError('must be string or list of strings')
        if isinstance(value, list) and any((not isinstance(x, str) for x in value)):
            raise KiPlotConfigurationError('all items in the list must be strings')
        self._pcb_related = True
        self._refs = Optionable.force_list(value)
        if not self._refs:
            raise KiPlotConfigurationError('nothing to update')

    def get_example():
        """ Returns a YAML value for the example config """
        return "QR1, QR2"

    def update_footprint(self, ref, name, s):
        logger.debug(f'Replacing {ref} using {name}')
        # Get the footprint from the lib
        res = name.split(':')
        if len(res) != 2:
            logger.warning(W_NOLIB+"Component `{ref}` without correct lib name {name}")
            return False
        lib_alias = self._aliases.get(res[0])
        if lib_alias is None:
            raise KiPlotConfigurationError(f'Unknown library `{res[0]}`')
        fname = os.path.join(lib_alias.uri, res[1]+'.kicad_mod')
        if not os.path.isfile(fname):
            raise KiPlotConfigurationError(f'Missing footprint `{res[1]}` in `{res[0]}` lib')
        logger.debug(f'- Lib file {fname}')
        c = load_sexp_file(fname)
        # Which attributes we want to keep from the original PCB
        attrs = KICAD8_ATTRS if GS.ki8 else KICAD6_ATTRS
        # Keep the attributes like UUID/tstamp, position, properties, etc.
        keep = list(filter(lambda s: keep_attr(attrs, s), s))
        # Get the other attributes from the lib version
        from_lib = list(filter(lambda s: not keep_attr(attrs, s), c[0]))
        # Replace the footprint using the combination
        s[:] = keep+from_lib
        return True

    def apply(self):
        pcb = load_sexp_file(GS.pcb_file)
        self._aliases = KiConf.get_fp_lib_aliases()
        updated = False
        # Look for all modules (KiCad 6) and/or footprints (KiCad 7)
        for iter in [sexp_iter(pcb, 'kicad_pcb/module'), sexp_iter(pcb, 'kicad_pcb/footprint')]:
            for fp in iter:
                # The first value is the name LIB:FP
                fp_name = _check_relaxed(fp, 1, 'footprint name')
                # Look for the reference of this footprint
                for s in fp[2:]:
                    # fp_text/property (KiCad 8) named "reference"
                    if _get_symbol_name(s) in ('fp_text', 'property') and \
                       _check_relaxed(s, 1, 'property name').lower() == 'reference':
                        # Check if this reference needs update
                        ref = _check_relaxed(s, 2, 'property value')
                        if ref in self._refs:
                            updated |= self.update_footprint(ref, fp_name, fp)
        # If we replaced one or more footprints
        if updated:
            save_pcb_from_sexp(pcb, logger)
