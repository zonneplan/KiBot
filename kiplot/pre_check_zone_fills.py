from .pre_base import (BasePreFlight)
from .error import (KiPlotConfigurationError)


class CheckZoneFills(BasePreFlight):
    """ [boolean=false] Zones are filled before doing any operation involving PCB layers """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._pcb_related = True

    def run(self):
        pass

    def apply(self):
        BasePreFlight._set_option('check_zone_fills', self._enabled)


# Register it
BasePreFlight.register('check_zone_fills', CheckZoneFills)
