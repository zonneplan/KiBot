from .optionable import Optionable
from . import log

logger = log.get_logger(__name__)


class BaseOutput(Optionable):
    _registered = {}

    def __init__(self, name, type, description):
        super().__init__(name, description)
        self._type = type
        self._sch_related = False
        self._unkown_is_error = False

    def config(self, outdir, options, layers):
        self._outdir = outdir
        self._layers = layers
        super().config(options)

    @staticmethod
    def attr2longopt(attr):
        return '--'+attr.replace('_', '-')

    @staticmethod
    def register(name, aclass):
        BaseOutput._registered[name] = aclass

    @staticmethod
    def is_registered(name):
        return name in BaseOutput._registered

    @staticmethod
    def get_class_for(name):
        return BaseOutput._registered[name]

    @staticmethod
    def get_registered():
        return BaseOutput._registered

    def __str__(self):
        return "'{}' ({}) [{}]".format(self._description, self._name, self._type)

    def is_sch(self):
        """ True for outputs that works on the schematic """
        return self._sch_related

    def is_pcb(self):
        """ True for outputs that works on the PCB """
        return not self._sch_related

    def read_vals_from_po(self, po):
        """ Set attributes from a PCB_PLOT_PARAMS (plot options) """
        return

    # These get_* aren't really needed.
    # _* members aren't supposed to be used by the user, not the code.
    def get_name(self):
        return self._name

    def get_outdir(self):
        return self._outdir

    def run(self, output_dir, board):  # pragma: no cover
        logger.error("The run member for the class for the output type `{}` isn't implemented".format(self._type))
