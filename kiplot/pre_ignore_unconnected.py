from .pre_base import (BasePreFlight)
from .error import (KiPlotConfigurationError)


class IgnoreUnconnected(BasePreFlight):
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._pcb_related = True

    def run(self, brd_file):
        pass

    def apply(self):
        BasePreFlight._set_option('ignore_unconnected', self._enabled)


# Register it
BasePreFlight.register('ignore_unconnected', IgnoreUnconnected)
