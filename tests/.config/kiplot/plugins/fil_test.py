from kibot.macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


with document:
    avar = 1
    """ Documentation """
    bvar = True
    """ Other doc """
assert _help_avar == '[number=1] Documentation', _help_avar
assert _help_bvar == '[boolean=true] Other doc', _help_bvar

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
