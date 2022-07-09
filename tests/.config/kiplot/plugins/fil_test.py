from kibot.macros import macros, document, filter_class  # noqa: F401
from . import log
from .gs import GS

logger = log.get_logger(__name__)


with document:
    avar = GS.test_number
    """ Documentation """
    bvar = GS.test_boolean
    """ Other doc """
assert _help_avar == '[number=5] Documentation. Affected by global options', _help_avar  # noqa: F821
assert _help_bvar == '[boolean=true] Other doc. Affected by global options', _help_bvar  # noqa: F821
logger.debug('Test filter imported, assertions passed, debug_level: {}'.format(GS.debug_level))
logger.debug('_help_avar: {}'.format(_help_avar))  # noqa: F821


@filter_class
def pp():
    pass


@filter_class
class Filter_Test(BaseFilter):  # noqa: F821
    def __init__(self):
        super().__init__()
        with document:
            self.foo = ':'
            self.bar = False
            """ Rename fields matching the variant to the value of the component """
