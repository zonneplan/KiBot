from kibot.macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


@filter_class
class Filter_Test(BaseFilter):  # noqa: F821
    def __init__(self):
        super().__init__()
        with document:
            self.foo = ':'
            self.bar = False
            """ Rename fields matching the variant to the value of the component """
