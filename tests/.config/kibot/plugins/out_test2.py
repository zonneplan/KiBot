from .optionable import BaseOptions
from kibot.macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class TestOptions(BaseOptions):
    def __init__(self):
        super().__init__()
        with document:
            self.foo = True
            """ frutilla """
            self.bar = 'nope'
            """ todo """  # pragma: no cover


@output_class
class Test2(BaseOutput):  # noqa: F821
    """ Test for plugin
        A loadable output.
        Nothing useful, just a test. """
    def __init__(self):
        super().__init__()
        logger.debug('Creating a test')
        with document:
            self.options = TestOptions
            """ [dict] Options for the `test` output """  # pragma: no cover
