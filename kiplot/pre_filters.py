import os
from .kiplot import (GS)
from kiplot.macros import macros, pre_class  # noqa: F401


@pre_class
class Filters(BasePreFlight):  # noqa: F821
    """ A list of entries to filter out ERC/DRC messages. Keys: `filter`, `number` and `regex` """
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
