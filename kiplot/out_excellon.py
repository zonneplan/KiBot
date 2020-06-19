from pcbnew import (EXCELLON_WRITER)
from .out_base import (BaseOutput)
from .out_any_drill import (AnyDrill)


class Excellon(AnyDrill):
    def __init__(self, name, type, description):
        super(Excellon, self).__init__(name, type, description)
        self.metric_units = True
        self.pth_and_npth_single_file = True
        self.minimal_header = False
        self.mirror_y_axis = False

    def _configure_writer(self, board, offset):
        drill_writer = EXCELLON_WRITER(board)
        drill_writer.SetOptions(self.mirror_y_axis, self.minimal_header, offset, self.pth_and_npth_single_file)
        drill_writer.SetFormat(self.metric_units, EXCELLON_WRITER.DECIMAL_FORMAT)
        return drill_writer


# Register it
BaseOutput.register('excellon', Excellon)
