import os
from .kiplot import (GS)
from .pre_base import (BasePreFlight)


class Filters(BasePreFlight):
    def __init__(self, name, value):
        super().__init__(name, value)

    def run(self):
        pass

    def apply(self):
        # Create the filters file
        if self._value:
            GS.filter_file = os.path.join(GS.out_dir, 'kiplot_errors.filter')
            with open(GS.filter_file, 'w') as f:
                f.write(self._value)


# Register it
BasePreFlight.register('filters', Filters)
