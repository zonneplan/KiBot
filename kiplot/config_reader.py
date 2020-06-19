"""
Class to read KiPlot config files
"""

import re
import sys

import pcbnew

from .error import (KiPlotConfigurationError)
from .kiplot import (Layer, get_layer_id_from_pcb)
from .misc import (NO_YAML_MODULE, EXIT_BAD_CONFIG)
# Output classes
from .out_base import BaseOutput
from . import out_gerber          # noqa: F401
from . import out_ps              # noqa: F401
from . import out_hpgl            # noqa: F401
from . import out_dxf             # noqa: F401
from . import out_pdf             # noqa: F401
from . import out_svg             # noqa: F401
from . import out_gerb_drill      # noqa: F401
from . import out_excellon        # noqa: F401
from . import out_position        # noqa: F401
from . import out_step            # noqa: F401
from . import out_kibom           # noqa: F401
from . import out_ibom            # noqa: F401
from . import out_pdf_sch_print   # noqa: F401
from . import out_pdf_pcb_print   # noqa: F401
# PreFlight classes
from .pre_base import BasePreFlight
from . import pre_drc                 # noqa: F401
from . import pre_erc                 # noqa: F401
from . import pre_update_xml          # noqa: F401
from . import pre_check_zone_fills    # noqa: F401
from . import pre_ignore_unconnected  # noqa: F401
from . import pre_filters             # noqa: F401
# Logger
from . import log

logger = log.get_logger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover
    log.init(False, False)
    logger.error('No yaml module for Python, install python3-yaml')
    sys.exit(NO_YAML_MODULE)


def config_error(msg):
    logger.error(msg)
    sys.exit(EXIT_BAD_CONFIG)


class CfgYamlReader(object):
    def __init__(self, brd_file):
        super(CfgYamlReader, self).__init__()

    def _check_version(self, v):
        if not isinstance(v, dict):
            config_error("Incorrect `kiplot` section")
        if 'version' not in v:
            config_error("YAML config needs `kiplot.version`.")
        version = v['version']
        # Only version 1 is known
        if version != 1:
            config_error("Unknown KiPlot config version: "+str(version))
        return version

    def _get_layer_from_str(self, s):
        """
        Get the pcbnew layer from a string in the config
        """
        D = {
            'F.Cu': pcbnew.F_Cu,
            'B.Cu': pcbnew.B_Cu,
            'F.Adhes': pcbnew.F_Adhes,
            'B.Adhes': pcbnew.B_Adhes,
            'F.Paste': pcbnew.F_Paste,
            'B.Paste': pcbnew.B_Paste,
            'F.SilkS': pcbnew.F_SilkS,
            'B.SilkS': pcbnew.B_SilkS,
            'F.Mask': pcbnew.F_Mask,
            'B.Mask': pcbnew.B_Mask,
            'Dwgs.User': pcbnew.Dwgs_User,
            'Cmts.User': pcbnew.Cmts_User,
            'Eco1.User': pcbnew.Eco1_User,
            'Eco2.User': pcbnew.Eco2_User,
            'Edge.Cuts': pcbnew.Edge_Cuts,
            'Margin': pcbnew.Margin,
            'F.CrtYd': pcbnew.F_CrtYd,
            'B.CrtYd': pcbnew.B_CrtYd,
            'F.Fab': pcbnew.F_Fab,
            'B.Fab': pcbnew.B_Fab,
        }
        layer = None
        # Priority
        # 1) Internal list
        if s in D:
            layer = Layer(D[s], False, s)
        else:
            id = get_layer_id_from_pcb(s)
            if id is not None:
                # 2) List from the PCB
                layer = Layer(id, id < pcbnew.B_Cu, s)
            elif s.startswith("Inner"):
                # 3) Inner.N names
                m = re.match(r"^Inner\.([0-9]+)$", s)
                if not m:
                    raise KiPlotConfigurationError("Malformed inner layer name: {}, use Inner.N".format(s))
                layer = Layer(int(m.group(1)), True, s)
            else:
                raise KiPlotConfigurationError('Unknown layer name: '+s)
        return layer

    def _parse_layers(self, layers_to_parse):
        # Check we have a list of layers
        if not layers_to_parse:
            raise KiPlotConfigurationError("Missing `layers` definition")
        if not isinstance(layers_to_parse, list):
            raise KiPlotConfigurationError("`layers` must be a list")
        # Parse the elements
        layers = []
        for l in layers_to_parse:
            # Check they are dictionaries
            if not isinstance(l, dict):
                raise KiPlotConfigurationError("Malformed `layer` entry ({})".format(l))
            # Extract the attributes
            layer = None
            description = 'no desc'
            suffix = ''
            for k, v in l.items():
                if k == 'layer':
                    layer = v
                elif k == 'description':
                    description = v
                elif k == 'suffix':
                    suffix = v
                else:
                    raise KiPlotConfigurationError("Unknown {} attribute for `layer`".format(v))
            # Check we got the layer name
            if layer is None:
                raise KiPlotConfigurationError("Missing `layer` attribute for layer entry ({})".format(l))
            # Create an object for it
            layer = self._get_layer_from_str(layer)
            layer.set_extra(suffix, description)
            layers.append(layer)
        return layers

    def _parse_output(self, o_obj):
        # Default values
        name = None
        desc = None
        otype = None
        options = None
        outdir = '.'
        layers = []
        # Parse all of them
        for k, v in o_obj.items():
            if k == 'name':
                name = v
            elif k == 'comment':
                desc = v
            elif k == 'type':
                otype = v
            elif k == 'options':
                options = v
            elif k == 'dir':
                outdir = v
            elif k == 'layers':
                layers = v
            else:
                config_error("Unknown key `{}` in `{}` ({})".format(k, name, otype))
        # Validate them
        if not name:
            config_error("Output needs a name in: "+str(o_obj))
        if not otype:
            config_error("Output `"+name+"` needs a type")
        name_type = "`"+name+"` ("+otype+")"

        # Is a valid type?
        if not BaseOutput.is_registered(otype):
            config_error("Unknown output type: `{}`".format(otype))
        # Load it
        logger.debug("Parsing output options for "+name_type)
        o_out = BaseOutput.get_class_for(otype)(name, otype, desc)
        # Apply the options
        try:
            # If we have layers parse them
            if layers:
                layers = self._parse_layers(layers)
            o_out.config(outdir, options, layers)
        except KiPlotConfigurationError as e:
            config_error("In section '"+name+"' ("+otype+"): "+str(e))

        return o_out

    def _parse_filters(self, filters):
        if not isinstance(filters, list):
            config_error("'filters' must be a list")
        parsed = None
        for filter in filters:
            if 'filter' in filter:
                comment = filter['filter']
                if 'number' in filter:
                    number = filter['number']
                    if number is None:
                        config_error("empty 'number' in 'filter' definition ("+str(filter)+")")
                else:
                    config_error("missing 'number' for 'filter' definition ("+str(filter)+")")
                if 'regex' in filter:
                    regex = filter['regex']
                    if regex is None:
                        config_error("empty 'regex' in 'filter' definition ("+str(filter)+")")
                else:
                    config_error("missing 'regex' for 'filter' definition ("+str(filter)+")")
                logger.debug("Adding DRC/ERC filter '{}','{}','{}'".format(comment, number, regex))
                if parsed is None:
                    parsed = ''
                if not comment:
                    parsed += '# '+comment+'\n'
                parsed += '{},{}\n'.format(number, regex)
            else:
                config_error("'filters' section of 'preflight' must contain 'filter' definitions (not "+str(filter)+")")
        return parsed

    def _parse_preflight(self, pf):
        logger.debug("Parsing preflight options: {}".format(pf))
        if not isinstance(pf, dict):
            config_error("Incorrect `preflight` section")

        for k, v in pf.items():
            if not BasePreFlight.is_registered(k):
                config_error("Unknown preflight: `{}`".format(k))
            try:
                logger.debug("Parsing preflight "+k)
                if k == 'filters':
                    v = self._parse_filters(v)
                o_pre = BasePreFlight.get_class_for(k)(k, v)
            except KiPlotConfigurationError as e:
                config_error("In preflight '"+k+"': "+str(e))
            BasePreFlight.add_preflight(o_pre)

    def read(self, fstream):
        """
        Read a file object into a config object

        :param fstream: file stream of a config YAML file
        """
        try:
            data = yaml.load(fstream)
        except yaml.YAMLError as e:
            config_error("Error loading YAML "+str(e))
        # List of outputs
        outputs = []
        version = None
        # Analize each section
        for k, v in data.items():
            # logger.debug('{} {}'.format(k, v))
            if k == 'kiplot':
                version = self._check_version(v)
            elif k == 'preflight':
                self._parse_preflight(v)
            elif k == 'outputs':
                if isinstance(v, list):
                    for o in v:
                        outputs.append(self._parse_output(o))
                else:
                    config_error("`outputs` must be a list")
            else:
                logger.warning('Skipping unknown `{}` section in config.'.format(k))
        if version is None:
            config_error("YAML config needs `kiplot.version`.")
        return outputs
