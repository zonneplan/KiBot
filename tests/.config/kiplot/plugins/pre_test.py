from kibot.macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


@pre_class
class Pre_Test(BasePreFlight):  # noqa: F821
    """ Pre Test
        A preflight just for testing purposes """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.pre_test = False
            """ Enable this preflight """
