from kibot.macros import macros, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


@pre_class
class Pre_Test(BasePreFlight):  # noqa: F821
    def __init__(self, name, value):
        super().__init__(name, value)
        self._enabled = value
        self._pcb_related = True
