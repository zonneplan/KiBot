from .optionable import BaseOptions
from kibot.macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class TestOptions(BaseOptions):
    def __init__(self):
        super().__init__()
        with document:
            self.foo = True
            """ chocolate """
            self.not_documented = 1
            self.bar = 'nope'
            """ nothing """  # pragma: no cover

    def get_targets(self, out_dir):
        return ['dummy']


@output_class
class Test(BaseOutput):  # noqa: F821
    def __init__(self):
        super().__init__()
        logger.debug('Creating a test')
        with document:
            self.options = TestOptions
            """ [dict={}] Options for the `test` output """  # pragma: no cover

    def run(self, output_dir):
        logger.debug("Running test plug-in with "+output_dir)

    def get_dependencies(self):
        return ['dummy']
